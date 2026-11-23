"""Triggers for the engineering agents: failed runs, new pull requests, and Slack approvals."""

import contextlib
import copy
import fcntl
import json
import os
import re
import shlex
import subprocess
import time

import dagster as dg
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from hooli_agents import github_scope as gh
from hooli_agents import ledger, ops_tools, settings

STATE_PATH = ledger.VAR_DIR / "pr_state.json"
APPROVE_EMOJI = "white_check_mark"
REJECT_EMOJI = "x"
WATCH_HOURS = 24


bug_fix_job = dg.define_asset_job("bug_fix_job", selection=["bug_fixer", "bug_fixer_reply", "bug_fixer_outcome"])
pr_review_job = dg.define_asset_job("pr_review_job", selection=["pr_reviewer", "pr_reviewer_reply", "pr_reviewer_outcome"])
improvement_review_job = dg.define_asset_job(
    "improvement_review_job",
    selection=[
        "improvement_advisor",
        "improvement_advisor_reply",
        "improvement_advisor_outcome",
    ],
)


def _slack() -> WebClient:
    return WebClient(token=os.environ["SLACK_BOT_TOKEN"])


def _load() -> dict:
    return json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else {"prs": {}}


@contextlib.contextmanager
def _locked():
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH.with_suffix(".lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def _patch(number: str, changes: dict | None = None, create: dict | None = None) -> None:
    """Update one PR's entry under a lock, so two sensors never overwrite each other's changes."""
    with _locked():
        state = _load()
        if create is not None:
            state["prs"][number] = create
        elif number in state["prs"]:
            state["prs"][number].update(changes or {})
        _save(state)


def _save(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state))
    tmp.replace(STATE_PATH)


def _run_url(run_id: str) -> str:
    return f"{settings.get('dagster_url', '')}/runs/{run_id}"


FAILED_RUN_IN_BODY = re.compile(r"(?:Fixes failed run|Run ID)[^0-9a-f]*([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", re.IGNORECASE)
VERIFY_TIMEOUT_MINUTES = 30
BRANCH_SKIP = "Branch deployment: the full deployment's sensors handle announcements and approvals."


def _in_branch_deployment() -> bool:
    """Dagster+ sets this in branch deployments, where a second copy of each sensor would double-post."""
    return os.environ.get("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "").lower() in ("1", "true")


def _start_verification(number: str, pr: dict, entry: dict) -> str:
    """After a merge: run the deploy hook, then re-execute the run the pull request says it fixes."""
    found = FAILED_RUN_IN_BODY.search(pr.get("body") or "")
    if not found:
        return ":grey_question: Merged, but the pull request does not name the failed run, so I could not verify it."
    failed_run = found.group(1)
    hook = settings.get("post_merge_command")
    if hook:
        done = subprocess.run(shlex.split(hook) if isinstance(hook, str) else hook, capture_output=True, text=True, timeout=120, check=False)
        if done.returncode:
            return f":warning: Merged, but the deploy step failed, so I did not verify: {done.stderr.strip()[:200]}"
    result = ops_tools._gql(
        "mutation($p:ReexecutionParams!){ launchRunReexecution(reexecutionParams:$p){ __typename "
        "... on LaunchRunSuccess { run { runId } } ... on PythonError { message } } }",
        {"p": {"parentRunId": failed_run, "strategy": "ALL_STEPS"}},
    )["launchRunReexecution"]
    if result["__typename"] != "LaunchRunSuccess":
        return f":warning: Merged, but I could not re-run {failed_run[:8]}: {result.get('message', result['__typename'])[:200]}"
    entry["verify"] = {"failed_run": failed_run, "run_id": result["run"]["runId"], "started": time.time(), "done": False}
    return f":arrows_counterclockwise: Merged. Re-running the failed run <{_run_url(failed_run)}|{failed_run[:8]}> to check the fix."


def _check_verification(entry: dict) -> str | None:
    """A message once the re-run finishes, or None while it is still going."""
    v = entry["verify"]
    status = ops_tools._gql("query($id:ID!){ runOrError(runId:$id){ ... on Run { status } } }", {"id": v["run_id"]})[
        "runOrError"
    ].get("status")
    link = f"<{_run_url(v['run_id'])}|the re-run>"
    if status == "SUCCESS":
        v["done"], v["result"] = True, "fixed"
        return f":white_check_mark: Verified: {link} of {v['failed_run'][:8]} succeeded, so the fix works."
    if status in ("FAILURE", "CANCELED"):
        v["done"], v["result"] = True, "still_failing"
        return f":x: Still failing after the fix: {link} {status.lower()}. A person needs to look."
    if time.time() - v["started"] > VERIFY_TIMEOUT_MINUTES * 60:
        v["done"], v["result"] = True, "timed_out"
        return f":hourglass: I could not confirm the fix: {link} did not finish in {VERIFY_TIMEOUT_MINUTES} minutes."
    return None


@dg.run_failure_sensor(
    name="failed_run_trigger",
    monitor_all_code_locations=True,
    request_job=bug_fix_job,
    default_status=dg.DefaultSensorStatus.RUNNING,
)
def failed_run_trigger(context: dg.RunFailureSensorContext):
    if _in_branch_deployment():
        return dg.SkipReason(BRANCH_SKIP)
    run = context.dagster_run
    origin = run.remote_job_origin
    location = origin.location_name if origin else None
    if not ops_tools.location_watched(location):
        return dg.SkipReason(f"Run {run.run_id[:8]} is not in a watched code location.")
    channel = settings.get("slack_channel")
    try:
        posted = _slack().chat_postMessage(
            channel=channel,
            text=(
                f":beetle: Run <{_run_url(run.run_id)}|{run.run_id[:8]}> of `{run.job_name}` "
                f"failed in `{location}`. Looking into the cause."
            ),
        )
    except SlackApiError as e:
        context.log.error(f"Could not post to Slack channel {channel}: {e.response.get('error')}")
        return dg.SkipReason("Slack post failed.")
    return dg.RunRequest(
        run_key=run.run_id,
        tags={
            "eng/failed_run_id": run.run_id,
            "slack/channel": channel,
            "slack/thread_ts": posted["ts"],
        },
    )


@dg.sensor(
    name="new_pr_trigger",
    job=pr_review_job,
    minimum_interval_seconds=60,
    default_status=dg.DefaultSensorStatus.RUNNING,
)
def new_pr_trigger(context: dg.SensorEvaluationContext):
    if _in_branch_deployment():
        return dg.SkipReason(BRANCH_SKIP)
    state = _load()
    channel = settings.get("slack_channel")
    client = _slack()
    requests = []
    problems = []
    for pr in gh.open_pull_requests():
        sha = pr["head_sha"][:7]
        existing = state["prs"].get(str(pr["number"]))
        if existing and existing["sha"] == sha:
            continue
        try:
            posted = client.chat_postMessage(
                channel=channel,
                text=(
                    f":mag: Pull request <{pr['url']}|#{pr['number']} {pr['title']}> by {pr['author']}. "
                    f"Reviewing now. If it needs a person, react :{APPROVE_EMOJI}: to approve "
                    f"or :{REJECT_EMOJI}: to request changes."
                ),
            )
            for emoji in (APPROVE_EMOJI, REJECT_EMOJI):
                client.reactions_add(channel=channel, timestamp=posted["ts"], name=emoji)
        except SlackApiError as e:
            problems.append(f"Slack {e.response.get('error')} for channel {channel}")
            context.log.error(problems[-1])
            continue
        _patch(
            str(pr["number"]),
            create={
                "channel": channel,
                "ts": posted["ts"],
                "sha": sha,
                "status": "reviewing",
                "since": time.time(),
            },
        )
        requests.append(
            dg.RunRequest(
                run_key=f"pr-{pr['number']}-{sha}",
                tags={
                    "eng/pr_number": str(pr["number"]),
                    "slack/channel": channel,
                    "slack/thread_ts": posted["ts"],
                },
            )
        )
    if requests:
        return dg.SensorResult(run_requests=requests)
    return dg.SkipReason("; ".join(problems) or "No new pull requests.")


def _display_name(client: WebClient, user_id: str) -> str:
    try:
        profile = client.users_info(user=user_id)["user"]["profile"]
        return profile.get("display_name") or profile.get("real_name") or user_id
    except SlackApiError:
        return user_id


@dg.sensor(
    name="pr_approval_watcher",
    minimum_interval_seconds=30,
    default_status=dg.DefaultSensorStatus.RUNNING,
)
def pr_approval_watcher(context: dg.SensorEvaluationContext):
    if _in_branch_deployment():
        return dg.SkipReason(BRANCH_SKIP)
    state = _load()
    before = copy.deepcopy(state)
    client = _slack()
    bot_id = client.auth_test()["user_id"]
    auto_merge = bool(settings.get("auto_merge", False))
    merged_any = False

    def say(entry: dict, text: str) -> None:
        client.chat_postMessage(channel=entry["channel"], thread_ts=entry["ts"], text=text)

    for number, entry in state["prs"].items():
        if entry.get("verify") and not entry["verify"].get("done"):
            try:
                message = _check_verification(entry)
            except Exception as e:  # noqa: BLE001 -- a failed check must not stop the other pull requests
                context.log.error(f"Could not check the re-run for PR #{number}: {e}")
                message = None
            if message:
                say(entry, message)
        status = entry["status"]
        if status not in ("reviewing", "awaiting_human", "approved"):
            continue
        if status != "approved" and time.time() - entry["since"] > WATCH_HOURS * 3600:
            entry["status"] = "expired"
            continue
        try:
            pr = gh.get_pull_request(int(number))
        except gh.ScopeError as e:
            context.log.error(str(e))
            continue
        if pr["state"] != "open":
            entry["status"] = "merged" if pr.get("merged") else "closed"
            continue
        branch_url = pr.get("branch_deployment_url")
        if (
            status != "approved"
            and branch_url
            and branch_url != entry.get("branch_url")
            and gh.assess_risk(pr)["level"] != "low"
        ):
            entry["branch_url"] = branch_url
            say(entry, f":test_tube: A branch deployment of this change is ready to test: <{branch_url}|open it>")
        if status != "approved":
            if gh.approvals(int(number)):
                entry["status"] = status = "approved"
            else:
                reactions = client.reactions_get(channel=entry["channel"], timestamp=entry["ts"])["message"].get(
                    "reactions", []
                )
                votes = {r["name"]: [u for u in r["users"] if u != bot_id] for r in reactions}
                for emoji, approve in ((APPROVE_EMOJI, True), (REJECT_EMOJI, False)):
                    if not votes.get(emoji):
                        continue
                    who = votes[emoji][0]
                    try:
                        gh.human_decision(int(number), approve, _display_name(client, who))
                    except gh.ScopeError as e:
                        if entry.get("last_error") != str(e):
                            entry["last_error"] = str(e)
                            say(entry, f":warning: {e}")
                        break
                    entry["status"] = status = "approved" if approve else "changes_requested"
                    say(
                        entry,
                        f":white_check_mark: Approved on GitHub for <@{who}>."
                        if approve
                        else f":x: Changes requested on GitHub for <@{who}>.",
                    )
                    break
        if status == "approved" and auto_merge:
            try:
                gh.merge_if_ready(int(number))
            except gh.ScopeError as e:
                if "pending" not in str(e) and entry.get("last_error") != str(e):
                    entry["last_error"] = str(e)
                    say(entry, f":warning: Not merged: {e}")
            else:
                entry["status"] = "merged"
                merged_any = True
                say(entry, f":rocket: Merged #{number} into main.")
                if settings.get("verify_after_merge"):
                    try:
                        say(entry, _start_verification(number, pr, entry))
                    except Exception as e:  # noqa: BLE001
                        say(entry, f":warning: Merged, but verification could not start: {str(e)[:200]}")
    if merged_any:
        for n in gh.refresh_open_agent_prs():
            context.log.info(f"Updated branch of PR #{n} so CI runs against the merged code.")
    for number, entry in state["prs"].items():
        changes = {k: v for k, v in entry.items() if before["prs"].get(number, {}).get(k) != v}
        if changes:
            _patch(number, changes)
    return dg.SkipReason("Checked pending approvals.")


def _periodic_review(context: dg.SensorEvaluationContext, name: str, period_hours: float, text: str):
    """Fire once per period (the first tick fires at once), announcing in Slack and tagging the thread."""
    now = time.time()
    last = float(context.cursor) if context.cursor else 0.0
    if now - last < period_hours * 3600:
        return dg.SkipReason(f"Next {name} in {round((last + period_hours * 3600 - now) / 3600, 1)}h.")
    channel = settings.get("slack_channel")
    try:
        posted = _slack().chat_postMessage(channel=channel, text=text)
    except SlackApiError as e:
        context.log.error(f"Could not post to Slack channel {channel}: {e.response.get('error')}")
        return dg.SkipReason("Slack post failed.")
    return dg.SensorResult(
        run_requests=[
            dg.RunRequest(
                run_key=f"{name}-{int(now)}",
                tags={"slack/channel": channel, "slack/thread_ts": posted["ts"]},
            )
        ],
        cursor=str(now),
    )


@dg.sensor(
    name="improvement_review_trigger",
    job=improvement_review_job,
    minimum_interval_seconds=3600,
    default_status=dg.DefaultSensorStatus.RUNNING,
)
def improvement_review_trigger(context: dg.SensorEvaluationContext):
    if _in_branch_deployment():
        return dg.SkipReason(BRANCH_SKIP)
    return _periodic_review(
        context,
        "improvement review",
        float(settings.get("improvement_period_hours", 168)),
        ":bar_chart: Improvement review started. Checking retries, deprecated APIs, freshness, automation and alerts.",
    )


def _excerpt(body: str, limit: int = 320) -> str:
    """The analysis section of a ticket body, or its start, as a short Slack quote."""
    text = body
    low = body.lower()
    if "analysis" in low:
        text = body[low.index("analysis") :].split("\n", 1)[-1]
        cut = text.lower().find("suggested change")
        text = text[:cut] if cut > 0 else text
    text = " ".join(text.split())
    return (text[:limit] + "…") if len(text) > limit else text


@dg.sensor(
    name="new_issue_announcer",
    minimum_interval_seconds=60,
    default_status=dg.DefaultSensorStatus.RUNNING,
)
def new_issue_announcer(context: dg.SensorEvaluationContext):
    if _in_branch_deployment():
        return dg.SkipReason(BRANCH_SKIP)
    """Announce each new ticket the agents filed (GitHub Issues, and Linear when a team is set)."""
    from hooli_agents import linear_scope

    announced = set(json.loads(context.cursor)) if context.cursor else set()
    channel = settings.get("slack_channel")
    client = _slack()
    found = [("GitHub", i) for i in gh.list_agent_issues()]
    if settings.get("linear_team_id"):
        try:
            found += [("Linear", i) for i in linear_scope.list_agent_issues()]
        except linear_scope.LinearError as e:
            context.log.error(str(e))
    for source, issue in found:
        key = f"{source}:{issue['number']}"
        if key in announced:
            continue
        try:
            client.chat_postMessage(
                channel=channel,
                text=(
                    f":memo: {source} ticket <{issue['url']}|{issue['number']} {issue['title']}> "
                    f"filed by an engineering agent.\n> {_excerpt(issue['body'])}"
                ),
            )
        except SlackApiError as e:
            context.log.error(f"Slack {e.response.get('error')} for channel {channel}")
            continue
        announced.add(key)
    return dg.SensorResult(cursor=json.dumps(sorted(announced)))
