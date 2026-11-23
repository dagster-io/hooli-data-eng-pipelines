"""GitHub access limited to one repository, with the review rules enforced in code.

Tokens come from ENG_GITHUB_TOKEN and ENG_REVIEWER_GITHUB_TOKEN, or the `gh` CLI when those are unset, and
are never stored. Every call is pinned to REPO, so a prompt cannot point the agents at another repository.
"""

import base64
import os
import re
import subprocess
from functools import lru_cache

import requests

from hooli_agents import ledger, settings

REPO = settings.get("repo", "")
BASE_BRANCH = settings.get("base_branch", "main")
BRANCH_PREFIX = "agent/"
API = "https://api.github.com"

MAX_FILES_PER_FIX = 5
# The agents may not change CI, dependencies or packaging.
PROTECTED_NAMES = ("pyproject.toml", "requirements", "Dockerfile", "setup.", "uv.lock", "dagster_cloud")
LOW_RISK_MAX_FILES = 2


def is_protected(path: str) -> bool:
    """Protected at the repo root or inside any project folder of a monorepo."""
    parts = path.split("/")
    return path.startswith(".github/") or any(parts[-1].startswith(x) for x in PROTECTED_NAMES)


def is_low_risk(path: str) -> bool:
    parts = path.split("/")
    return any(x in parts[:-1] for x in ("src", "tests", "docs")) or parts[-1].startswith("README")
LOW_RISK_MAX_LINES = 30


class ScopeError(Exception):
    pass


@lru_cache(maxsize=4)
def _token(user: str | None) -> str:
    env_token = os.environ.get("ENG_REVIEWER_GITHUB_TOKEN" if user else "ENG_GITHUB_TOKEN")
    if env_token:
        return env_token
    cmd = ["gh", "auth", "token"] + (["--user", user] if user else [])
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
    if not out:
        raise ScopeError("No GitHub token found. Set ENG_GITHUB_TOKEN (and ENG_REVIEWER_GITHUB_TOKEN) or run `gh auth login`.")
    return out


def _call(method: str, path: str, *, user: str | None = None, **kwargs):
    resp = requests.request(
        method,
        f"{API}/repos/{REPO}{path}",
        headers={
            "Authorization": f"Bearer {_token(user)}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30,
        **kwargs,
    )
    if resp.status_code >= 400:
        raise ScopeError(f"GitHub {method} {path} failed ({resp.status_code}): {resp.text[:300]}")
    return resp.json() if resp.content else {}


def _reviewer() -> str:
    """The second GitHub login that approves; GitHub does not let an author approve their own PR."""
    user = settings.get("reviewer_gh_user")
    if not user:
        raise ScopeError("Set reviewer_gh_user (ENG_REVIEWER_GH_USER): a second GitHub login with write access.")
    return user


def _safe_path(path: str) -> str:
    path = path.strip().lstrip("/")
    if ".." in path.split("/") or path.startswith(".git/"):
        raise ScopeError(f"Invalid path: {path!r}")
    return path


def list_files(path: str = "") -> list[dict]:
    items = _call("GET", f"/contents/{_safe_path(path)}", params={"ref": BASE_BRANCH})
    items = items if isinstance(items, list) else [items]
    return [{"path": i["path"], "type": i["type"], "size": i.get("size")} for i in items]


def read_file(path: str, ref: str = BASE_BRANCH) -> str:
    item = _call("GET", f"/contents/{_safe_path(path)}", params={"ref": ref})
    return base64.b64decode(item["content"]).decode("utf-8")


def _apply_edit(path: str, edit: dict) -> str:
    """Replace one exact piece of the current file, so formatting everywhere else is untouched."""
    current = read_file(path)
    old, new = edit.get("old"), edit.get("new")
    if not old or new is None:
        raise ScopeError(f"{path}: give either content, or old and new text.")
    if current.count(old) != 1:
        raise ScopeError(f"{path}: the old text must appear exactly once (found {current.count(old)}).")
    return current.replace(old, new)


def propose_fix(
    branch: str, title: str, body: str, files: list[dict], note: str = "", kind: str = "fix"
) -> dict:
    if not files or len(files) > MAX_FILES_PER_FIX:
        raise ScopeError(f"A fix changes between 1 and {MAX_FILES_PER_FIX} files.")
    for f in files:
        p = _safe_path(f["path"])
        if is_protected(p):
            raise ScopeError(f"{p} is protected; agents may not change it.")
    wanted = {_safe_path(f["path"]) for f in files}
    for open_pr in _call("GET", "/pulls", params={"state": "open", "per_page": 50}):
        touched = {f["filename"] for f in _call("GET", f"/pulls/{open_pr['number']}/files", params={"per_page": 100})}
        if wanted & touched:
            raise ScopeError(
                f"PR #{open_pr['number']} ({open_pr['title']}) already changes {min(wanted & touched)}; "
                "do not open another for the same file."
            )
    if settings.shadow():
        ledger.record(
            "would_file", place="pull_request", title=title, body=body[:1500], files=sorted(wanted)
        )
        return {"practice_mode": True, "would_open": "pull_request", "title": title, "url": "(practice mode: nothing was opened)"}
    slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in branch)[:60].strip("-") or "fix"
    name = BRANCH_PREFIX + slug
    base_sha = _call("GET", f"/git/ref/heads/{BASE_BRANCH}")["object"]["sha"]
    _call("POST", "/git/refs", json={"ref": f"refs/heads/{name}", "sha": base_sha})
    for f in files:
        p = _safe_path(f["path"])
        try:
            existing = _call("GET", f"/contents/{p}", params={"ref": BASE_BRANCH})["sha"]
        except ScopeError:
            existing = None
        content = f["content"] if "content" in f else _apply_edit(p, f)
        payload = {
            "message": title,
            "content": base64.b64encode(content.encode()).decode(),
            "branch": name,
        }
        if existing:
            payload["sha"] = existing
        _call("PUT", f"/contents/{p}", json=payload)
    footer = f"\n\n---\nOpened by an engineering agent. Kind: {kind}. {note}".rstrip()
    pr = _call("POST", "/pulls", json={"title": title, "body": body + footer, "head": name, "base": BASE_BRANCH})
    ledger.record("pull_request", title=title, url=pr["html_url"], number=pr["number"], change_kind=kind)
    return {"number": pr["number"], "url": pr["html_url"], "branch": name}


def _checks(sha: str) -> dict:
    runs = _call("GET", f"/commits/{sha}/check-runs")["check_runs"]
    statuses = {r["name"]: (r["conclusion"] or r["status"]) for r in runs}
    if not statuses:
        return {"state": "none", "runs": {}}
    if any(v in ("failure", "cancelled", "timed_out") for v in statuses.values()):
        state = "failing"
    elif all(v == "success" for v in statuses.values()):
        state = "passing"
    else:
        state = "pending"
    return {"state": state, "runs": statuses}


def _require_agent_branch(pr: dict) -> None:
    if not pr["head"]["ref"].startswith(BRANCH_PREFIX):
        raise ScopeError(f"PR #{pr['number']} is not an agent branch ({BRANCH_PREFIX}*); agents leave other pull requests alone.")


def get_pull_request(number: int) -> dict:
    pr = _call("GET", f"/pulls/{int(number)}")
    _require_agent_branch(pr)
    files = _call("GET", f"/pulls/{int(number)}/files", params={"per_page": 100})
    return {
        "number": pr["number"],
        "url": pr["html_url"],
        "title": pr["title"],
        "body": pr["body"],
        "author": pr["user"]["login"],
        "state": pr["state"],
        "merged": bool(pr.get("merged")),
        "head_sha": pr["head"]["sha"],
        "head_ref": pr["head"]["ref"],
        "files": [
            {
                "path": f["filename"],
                "status": f["status"],
                "additions": f["additions"],
                "deletions": f["deletions"],
                "patch": (f.get("patch") or "")[:6000],
            }
            for f in files
        ],
        "checks": _checks(pr["head"]["sha"]),
        "branch_deployment_url": branch_deployment_url(pr["number"], pr["head"]["sha"]),
    }


def assess_risk(pr: dict) -> dict:
    """Deterministic risk level for a PR; the model may describe it but cannot change it."""
    reasons: list[str] = []
    files = pr["files"]
    changed = sum(f["additions"] + f["deletions"] for f in files)
    if len(files) > LOW_RISK_MAX_FILES:
        reasons.append(f"changes {len(files)} files (limit {LOW_RISK_MAX_FILES})")
    if changed > LOW_RISK_MAX_LINES:
        reasons.append(f"changes {changed} lines (limit {LOW_RISK_MAX_LINES})")
    for f in files:
        if is_protected(f["path"]):
            reasons.append(f"touches protected path {f['path']}")
        elif not is_low_risk(f["path"]):
            reasons.append(f"touches {f['path']}, outside source, tests and docs")
    if pr["checks"]["state"] != "passing":
        reasons.append(f"checks are {pr['checks']['state']}")
    if "Kind: improvement" in (pr.get("body") or ""):
        reasons.append("it is an improvement proposal, which changes behavior, so a person decides")
    return {"level": "low" if not reasons else "needs_human", "reasons": reasons, "changed_lines": changed}


def review_pull_request(number: int, decision: str, body: str) -> dict:
    """COMMENT is always allowed. APPROVE only passes the low-risk rules, and uses the reviewer login."""
    pr = get_pull_request(number)
    risk = assess_risk(pr)
    decision = decision.upper()
    if decision not in ("COMMENT", "APPROVE"):
        raise ScopeError("decision must be COMMENT or APPROVE.")
    if decision == "APPROVE" and risk["level"] != "low":
        raise ScopeError("Not approved; a person must approve this one: " + "; ".join(risk["reasons"]))
    reviewer = _reviewer()
    _call(
        "POST",
        f"/pulls/{int(number)}/reviews",
        user=reviewer if decision == "APPROVE" else None,
        json={"event": decision, "body": body, "commit_id": pr["head_sha"]},
    )
    return {"number": number, "decision": decision, "risk": risk}


def open_pull_requests() -> list[dict]:
    prs = [p for p in _call("GET", "/pulls", params={"state": "open", "per_page": 100}) if p["head"]["ref"].startswith(BRANCH_PREFIX)]
    return [
        {
            "number": p["number"],
            "head_sha": p["head"]["sha"],
            "title": p["title"],
            "url": p["html_url"],
            "author": p["user"]["login"],
        }
        for p in prs
    ]


def approvals(number: int) -> list[str]:
    reviews = _call("GET", f"/pulls/{int(number)}/reviews", params={"per_page": 100})
    latest: dict[str, str] = {}
    for r in reviews:
        latest[r["user"]["login"]] = r["state"]
    return [u for u, state in latest.items() if state == "APPROVED"]


def human_decision(number: int, approve: bool, by: str) -> dict:
    """Record a person's decision made in Slack. Approval is refused while CI is failing."""
    pr = get_pull_request(number)
    if pr["state"] != "open":
        raise ScopeError(f"PR #{number} is {pr['state']}.")
    if approve and pr["checks"]["state"] == "failing":
        raise ScopeError("CI is failing, so this was not approved.")
    event = "APPROVE" if approve else "REQUEST_CHANGES"
    body = f"{'Approved' if approve else 'Changes requested'} by {by} in Slack."
    _call(
        "POST",
        f"/pulls/{int(number)}/reviews",
        user=_reviewer(),
        json={"event": event, "body": body, "commit_id": pr["head_sha"]},
    )
    return {"number": number, "decision": event}


def merge_if_ready(number: int) -> dict:
    """Squash-merge an agent PR that the second reviewer approved and whose checks pass."""
    pr = get_pull_request(number)
    if pr["state"] != "open":
        raise ScopeError(f"PR #{number} is {pr['state']}.")
    if not pr["head_ref"].startswith(BRANCH_PREFIX):
        raise ScopeError("Only agent branches are merged automatically.")
    if _reviewer() not in approvals(number):
        raise ScopeError("Not approved by the reviewer yet.")
    if pr["checks"]["state"] != "passing":
        raise ScopeError(f"Checks are {pr['checks']['state']}.")
    _call("PUT", f"/pulls/{int(number)}/merge", json={"merge_method": "squash", "sha": pr["head_sha"]})
    try:
        _call("DELETE", f"/git/refs/heads/{pr['head_ref']}")
    except ScopeError:
        pass
    return {"number": number, "merged": True}


def refresh_open_agent_prs() -> list[int]:
    """Bring open agent branches up to date with main so CI runs against the merged code."""
    updated = []
    for pr in _call("GET", "/pulls", params={"state": "open", "per_page": 50}):
        if not pr["head"]["ref"].startswith(BRANCH_PREFIX):
            continue
        try:
            _call("PUT", f"/pulls/{pr['number']}/update-branch", json={"expected_head_sha": pr["head"]["sha"]})
            updated.append(pr["number"])
        except ScopeError:
            pass
    return updated


ISSUE_LABEL = "engineering-agent"


def find_issues(query: str) -> list[dict]:
    """Open issues the agents filed whose title has any of the query's main words."""
    generic = {"dagster", "assets", "asset", "project", "improve", "improvements", "reliability", "update"}
    words = [w for w in dict.fromkeys(re.findall(r"[A-Za-z0-9_]{5,}", query.lower())) if w not in generic][:5]
    found: dict[int, dict] = {}
    for word in words:
        q = f"repo:{REPO} is:issue is:open label:{ISSUE_LABEL} {word} in:title"
        resp = requests.get(
            f"{API}/search/issues",
            params={"q": q, "per_page": 10},
            headers={"Authorization": f"Bearer {_token(None)}", "Accept": "application/vnd.github+json"},
            timeout=30,
        )
        if resp.status_code >= 400:
            raise ScopeError(f"Issue search failed ({resp.status_code}): {resp.text[:200]}")
        for i in resp.json()["items"]:
            found[i["number"]] = {"number": i["number"], "title": i["title"], "url": i["html_url"]}
    return list(found.values())


def open_issue(title: str, body: str, labels: list[str] | None = None) -> dict:
    if settings.shadow():
        ledger.record("would_file", place="github_issue", title=title, body=body[:1500])
        return {"practice_mode": True, "would_open": "github_issue", "title": title, "url": "(practice mode: nothing was filed)"}
    try:
        _call("POST", "/labels", json={"name": ISSUE_LABEL, "color": "1d76db"})
    except ScopeError:
        pass  # already exists
    extra = [x for x in (labels or []) if x and x != ISSUE_LABEL][:3]
    issue = _call(
        "POST",
        "/issues",
        json={"title": title, "body": body + "\n\n---\nFiled by an engineering agent.", "labels": [ISSUE_LABEL, *extra]},
    )
    ledger.record("github_issue", title=title, url=issue["html_url"], number=issue["number"])
    return {"number": issue["number"], "url": issue["html_url"]}


def list_agent_issues() -> list[dict]:
    """Open issues the agents filed, with their bodies, for announcing in Slack."""
    items = _call("GET", "/issues", params={"state": "open", "labels": ISSUE_LABEL, "per_page": 50})
    return [
        {"number": i["number"], "title": i["title"], "url": i["html_url"], "body": i.get("body") or ""}
        for i in items
        if "pull_request" not in i
    ]


_CLOUD_URL = re.compile(r"https://[A-Za-z0-9.-]*dagster\.cloud/[^\s)>\]\"']+")


def find_branch_deployment_url(texts: list[str]) -> str | None:
    """The Dagster+ branch deployment link in texts the Dagster Cloud action posts, if any.

    A link that names a deployment is preferred over a generic one (docs, the org home page).
    """
    found = []
    for text in texts:
        for match in _CLOUD_URL.findall(text or ""):
            url = match.rstrip(".,;")
            if "/docs" in url or "/settings" in url:
                continue
            found.append(url)
    for url in found:
        if re.search(r"/[^/]+--[^/]+|branch|/prod/|/deployment", url):
            return url
    return found[0] if found else None


def branch_deployment_url(number: int, head_sha: str) -> str | None:
    """Look in the PR comments, the check runs and the commit statuses for the branch deployment."""
    texts: list[str] = []
    for c in _call("GET", f"/issues/{int(number)}/comments", params={"per_page": 100}):
        texts.append(c.get("body") or "")
    for run in _call("GET", f"/commits/{head_sha}/check-runs")["check_runs"]:
        out = run.get("output") or {}
        texts += [run.get("details_url") or "", out.get("summary") or "", out.get("text") or ""]
    for st in _call("GET", f"/commits/{head_sha}/statuses"):
        texts += [st.get("target_url") or "", st.get("description") or ""]
    return find_branch_deployment_url(texts)
