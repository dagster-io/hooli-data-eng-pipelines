"""Triggers for the engineering agents: failed runs, weekly reviews and new-issue announcements."""

import json
import os
import time

import dagster as dg
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from hooli_agents import github_scope as gh
from hooli_agents import ops_tools, settings, triage


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


def _run_url(run_id: str) -> str:
    return f"{settings.get('dagster_url', '')}/runs/{run_id}"


BRANCH_SKIP = "Branch deployment: the full deployment's sensors handle announcements and approvals."


def _in_branch_deployment() -> bool:
    """Dagster+ sets this in branch deployments, where a second copy of each sensor would double-post."""
    return os.environ.get("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "").lower() in ("1", "true")


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
    instance = context.instance
    target = run.root_run_id or run.run_id
    if target != run.run_id and triage.analyzed_run(instance, target):
        return dg.SkipReason(f"Run {run.run_id[:8]} is a retry of {target[:8]}, which was already analyzed.")
    sig = triage.failure_signature(context, location)
    cooldown = float(settings.get("failure_cooldown_hours", 168))
    if triage.analyzed_recently(instance, sig, cooldown):
        return dg.SkipReason(f"Run {run.run_id[:8]} repeats a failure analyzed in the last {cooldown:g}h ({sig}).")
    cap = int(settings.get("max_analyses_per_day", 10))
    if triage.analyses_since(instance, 24) >= cap:
        return dg.SkipReason(f"Already analyzed {cap} failures in the last 24h; skipping {run.run_id[:8]}.")
    channel = settings.get("slack_channel")
    try:
        posted = _slack().chat_postMessage(
            channel=channel,
            text=(
                f":beetle: Run <{_run_url(target)}|{target[:8]}> of `{run.job_name}` "
                f"failed in `{location}`. Looking into the cause."
            ),
        )
    except SlackApiError as e:
        context.log.error(f"Could not post to Slack channel {channel}: {e.response.get('error')}")
        return dg.SkipReason("Slack post failed.")
    return dg.RunRequest(
        run_key=target,
        tags={
            "eng/failed_run_id": target,
            "eng/signature": sig,
            "slack/channel": channel,
            "slack/thread_ts": posted["ts"],
        },
    )


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
