"""Read-only evidence tools for the advisor agents: retry history and Dagster releases."""

import contextlib
import re
import time
from collections import defaultdict

import requests

from hooli_agents import settings

RUNS_QUERY = """query($limit:Int!){ runsOrError(limit:$limit){ ... on Runs { results { runId status pipelineName
  startTime tags { key value } repositoryOrigin { repositoryLocationName } } } } }"""
EVENTS_QUERY = """query($id:ID!){ logsForRun(runId:$id){ ... on EventConnection { events { __typename
  ... on ExecutionStepUpForRetryEvent { stepKey error { message cause { message } causes { message } } } } } } }"""


OWN_LOCATION = "hooli_agents"


def _in_location(run: dict) -> bool:
    """Whether a run belongs to the code location under review, not another one in the deployment."""
    origin = run.get("repositoryOrigin") or {}
    return location_watched(origin.get("repositoryLocationName"))


def watched_locations() -> list[str]:
    """Comma-separated ENG_WATCHED_LOCATION; empty means every code location in the deployment."""
    return [x.strip() for x in str(settings.get("watched_location", "") or "").split(",") if x.strip()]


def location_watched(name: str | None) -> bool:
    wanted = watched_locations()
    return bool(name) and name != OWN_LOCATION and (not wanted or name in wanted)


def _gql(query: str, variables: dict) -> dict:
    url = settings.get("dagster_graphql_url")
    if not url:
        raise RuntimeError("Set dagster_graphql_url (ENG_DAGSTER_GRAPHQL_URL).")
    resp = requests.post(
        url,
        json={"query": query, "variables": variables},
        headers={"Dagster-Cloud-Api-Token": settings.get("dagster_api_token", "")},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["data"]


def retry_report(days: int = 7, max_runs: int = 40) -> dict:
    """Steps that retried in recent runs: how often, why, and whether the run still succeeded."""
    cutoff = time.time() - days * 86400
    runs = _gql(RUNS_QUERY, {"limit": max_runs})["runsOrError"]["results"]
    base = (settings.get("dagster_url") or "").rstrip("/")
    steps: dict[str, dict] = defaultdict(lambda: {"runs_with_retries": 0, "retry_events": 0, "errors": {}, "run_ids": [], "outcomes": defaultdict(int)})
    scanned = 0
    for run in runs:
        if not _in_location(run) or (run["startTime"] and run["startTime"] < cutoff):
            continue
        scanned += 1
        events = _gql(EVENTS_QUERY, {"id": run["runId"]})["logsForRun"]["events"]
        per_step: dict[str, int] = defaultdict(int)
        for e in events:
            if e["__typename"] == "ExecutionStepUpForRetryEvent":
                per_step[e["stepKey"]] += 1
                err = e["error"] or {}
                chain = [c["message"] for c in (err.get("causes") or [])] or [(err.get("cause") or {}).get("message")]
                msg = (chain[-1] or err.get("message", "")).strip().splitlines()[-1][:240]
                steps[e["stepKey"]]["errors"][msg] = steps[e["stepKey"]]["errors"].get(msg, 0) + 1
        for step, n in per_step.items():
            rec = steps[step]
            rec["runs_with_retries"] += 1
            rec["retry_events"] += n
            rec["outcomes"][run["status"]] += 1
            rec["run_ids"].append(f"{base}/runs/{run['runId']}")
    return {
        "window_days": days,
        "runs_scanned": scanned,
        "steps": [
            {
                "step": step,
                "runs_with_retries": r["runs_with_retries"],
                "retry_events": r["retry_events"],
                "final_run_status": dict(r["outcomes"]),
                "errors": [{"message": m, "count": c} for m, c in sorted(r["errors"].items(), key=lambda x: -x[1])[:3]],
                "example_runs": r["run_ids"][:3],
            }
            for step, r in sorted(steps.items(), key=lambda x: -x[1]["retry_events"])
        ],
    }


def latest_dagster_release() -> dict:
    """The newest Dagster release and its notes, for judging whether new features are worth adopting."""
    pypi = requests.get("https://pypi.org/pypi/dagster/json", timeout=30).json()
    version = pypi["info"]["version"]
    notes = ""
    url = f"https://github.com/dagster-io/dagster/releases/tag/{version}"
    resp = requests.get(
        f"https://api.github.com/repos/dagster-io/dagster/releases/tags/{version}",
        headers={"Accept": "application/vnd.github+json"},
        timeout=30,
    )
    if resp.ok:
        notes = (resp.json().get("body") or "")[:6000]
        url = resp.json().get("html_url", url)
    return {"latest_version": version, "notes": notes, "url": url}


OVERVIEW_QUERY = """{
  assetNodes { assetKey { path } groupName jobNames
    freshnessPolicy { maximumLagMinutes cronSchedule }
    automationCondition { label }
    repository { location { name } } }
  alertPolicies { name description }
  workspaceOrError { ... on Workspace { locationEntries { name locationOrLoadError {
    ... on RepositoryLocation { dagsterLibraryVersions { name version } repositories { schedules { name cronSchedule pipelineName scheduleState { status } } } } } } } }
}"""


def list_locations() -> dict:
    """The code locations the advisor reviews: every watched one, or ENG_ADVISOR_LOCATION when set."""
    only = settings.get("advisor_location")
    entries = _gql("{ workspaceOrError { ... on Workspace { locationEntries { name loadStatus } } } }", {})["workspaceOrError"]["locationEntries"]
    names = [e["name"] for e in entries if location_watched(e["name"]) and (not only or e["name"] == only)]
    return {"locations": names}


def project_overview(location: str = "") -> dict:
    """Facts about one watched code location: assets, schedules, alerts, versions and recent retries."""
    from hooli_agents import github_scope

    location = location or settings.get("advisor_location") or ""
    if not location or not location_watched(location):
        raise RuntimeError("Pass a code location from list_locations.")
    data = _gql(OVERVIEW_QUERY, {})
    schedules = []
    running = None
    libraries: list[dict] = []
    for entry in data["workspaceOrError"]["locationEntries"]:
        if entry["name"] != location:
            continue
        for lib in (entry["locationOrLoadError"] or {}).get("dagsterLibraryVersions", []):
            libraries.append(lib)
            if lib["name"] == "dagster":
                running = lib["version"]
        for repo in (entry["locationOrLoadError"] or {}).get("repositories", []):
            for s in repo["schedules"]:
                schedules.append(
                    {"name": s["name"], "cron": s["cronSchedule"], "job": s["pipelineName"], "status": s["scheduleState"]["status"]}
                )
    assets = []
    for node in data["assetNodes"]:
        if node["repository"]["location"]["name"] != location:
            continue
        jobs = [j for j in node["jobNames"] if not j.startswith("__")]
        assets.append(
            {
                "asset_key": node["assetKey"]["path"],
                "group": node["groupName"],
                "freshness_policy": node["freshnessPolicy"],
                "automation_condition": (node["automationCondition"] or {}).get("label"),
                "scheduled_by": [s["name"] for s in schedules if s["job"] in jobs],
            }
        )
    constraint = None
    with contextlib.suppress(github_scope.ScopeError):
        found = re.search(r'"(dagster[^"]*)"', github_scope.read_file("pyproject.toml"))
        constraint = found.group(1) if found else None
    return {
        "code_location": location,
        "assets": assets,
        "schedules": schedules,
        "alert_policies": [{"name": a["name"], "description": a["description"]} for a in data["alertPolicies"]],
        "alert_policy_count": len(data["alertPolicies"]),
        "dagster_dependency": constraint,
        "running_dagster_version": running,
        "latest_dagster_version": latest_dagster_release()["latest_version"],
        "retries_last_7_days": retry_report(7),
        "partitions_and_checks": partition_and_check_health(location),
        "runtime_changes": runtime_changes(),
        "dependencies": dependency_report(libraries),
        "incidents_last_24h": incidents_last_24h(),
    }


def check_dagster_api(names: list[str]) -> dict:
    """Whether Dagster names exist in the installed version, with their signatures."""
    import importlib
    import inspect

    import dagster

    result: dict = {"dagster_version": dagster.__version__, "names": {}}
    for name in names[:12]:
        parts = name.replace("dg.", "dagster.", 1).split(".")
        try:
            obj = importlib.import_module(parts[0])
            for part in parts[1:]:
                obj = getattr(obj, part)
        except (ImportError, AttributeError):
            result["names"][name] = {"exists": False}
            continue
        try:
            signature = str(inspect.signature(obj))
        except (TypeError, ValueError):
            signature = None
        result["names"][name] = {"exists": True, "signature": signature}
    return result


def _resolve_dagster(chain: list[str], aliases: dict[str, str]):
    """Resolve a dotted name rooted at `dagster` or an alias of it, one hop at a time."""
    import importlib

    root = aliases.get(chain[0])
    if root is None:
        return None, "unrooted"
    obj = importlib.import_module(root.split(".")[0])
    for part in root.split(".")[1:] + chain[1:2]:
        if not hasattr(obj, part):
            return None, "missing"
        obj = getattr(obj, part)
    return obj, "ok"


def _scan_source(path: str, source: str) -> list[dict]:
    import ast

    from dagster import _annotations as ann

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    aliases: dict[str, str] = {}
    findings: list[dict] = []

    def judge(obj, name: str, line: int, param: str | None = None) -> None:
        info = ann.get_deprecated_info(obj) if ann.is_deprecated(obj) else None
        sup = ann.get_superseded_info(obj) if ann.is_superseded(obj) else None
        if param is not None:
            if param in (ann.get_deprecated_params(obj) if ann.has_deprecated_params(obj) else set()):
                pinfo = ann.get_deprecated_param_info(obj, param)
                findings.append(
                    {"path": path, "line": line, "name": f"{name}({param}=...)", "status": "deprecated parameter",
                     "breaking_version": getattr(pinfo, "breaking_version", None),
                     "note": getattr(pinfo, "additional_warn_text", None)}
                )
            return
        if info:
            findings.append(
                {"path": path, "line": line, "name": name, "status": "deprecated",
                 "breaking_version": info.breaking_version, "note": info.additional_warn_text}
            )
        elif sup:
            findings.append(
                {"path": path, "line": line, "name": name, "status": "superseded",
                 "breaking_version": None, "note": getattr(sup, "additional_warn_text", None)}
            )

    def chain_of(node) -> list[str] | None:
        parts: list[str] = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            return [node.id, *reversed(parts)]
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] == "dagster":
                    aliases[a.asname or a.name.split(".")[0]] = "dagster"
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == "dagster":
            for a in node.names:
                aliases[a.asname or a.name] = f"{node.module}.{a.name}"
    seen: set[tuple[int, str]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == "dagster":
            import importlib

            module = importlib.import_module(node.module)
            for a in node.names:
                if not hasattr(module, a.name):
                    findings.append({"path": path, "line": node.lineno, "name": f"{node.module}.{a.name}",
                                     "status": "removed", "breaking_version": None, "note": "no longer exists"})
                else:
                    judge(getattr(module, a.name), f"{node.module}.{a.name}", node.lineno)
        chain = chain_of(node) if isinstance(node, ast.Attribute) else None
        if chain and chain[0] in aliases and len(chain) >= 2 and aliases[chain[0]] == "dagster":
            obj, state = _resolve_dagster(chain, aliases)
            key = (node.lineno, ".".join(chain[:2]))
            if key in seen or isinstance(node.value, ast.Attribute):
                continue
            seen.add(key)
            if state == "missing":
                findings.append({"path": path, "line": node.lineno, "name": f"dagster.{chain[1]}",
                                 "status": "removed", "breaking_version": None, "note": "no longer exists"})
            elif obj is not None:
                judge(obj, f"dagster.{chain[1]}", node.lineno)
        if isinstance(node, ast.Call):
            fchain = chain_of(node.func) if isinstance(node.func, ast.Attribute) else (
                [node.func.id] if isinstance(node.func, ast.Name) else None)
            if fchain:
                obj, state = _resolve_dagster(fchain, aliases) if len(fchain) > 1 else (None, "unrooted")
                if len(fchain) == 1 and fchain[0] in aliases and aliases[fchain[0]] != "dagster":
                    import importlib

                    mod, _, attr = aliases[fchain[0]].rpartition(".")
                    obj, state = getattr(importlib.import_module(mod), attr, None), "ok"
                if obj is not None and state == "ok":
                    for kw in node.keywords:
                        if kw.arg:
                            judge(obj, ".".join(fchain), node.lineno, param=kw.arg)
            # decorators with keywords are Call nodes too, so they are covered above
    return findings


def deprecation_report(max_files: int = 40) -> dict:
    """Removed, deprecated or superseded Dagster APIs used in the repository's Python files."""
    import dagster

    from hooli_agents import github_scope

    tree = github_scope._call("GET", f"/git/trees/{github_scope.BASE_BRANCH}", params={"recursive": "1"})
    paths = [t["path"] for t in tree["tree"] if t["type"] == "blob" and t["path"].endswith(".py") and not github_scope.is_excluded(t["path"])][:max_files]
    findings: list[dict] = []
    for path in paths:
        findings += _scan_source(path, github_scope.read_file(path))
    unique = {(f["path"], f["line"], f["name"]): f for f in findings}
    return {
        "checked_against_dagster": dagster.__version__,
        "files_scanned": len(paths),
        "findings": sorted(unique.values(), key=lambda f: (f["path"], f["line"])),
    }


HEALTH_QUERY = """{
  assetNodes { assetKey { path } hasAssetChecks
    partitionStats { numMaterialized numPartitions numFailed numMaterializing }
    repository { location { name } } }
  runsOrError(limit: 100) { ... on Runs { results { runId status pipelineName startTime endTime
    assetSelection { path } repositoryOrigin { repositoryLocationName } } } }
}"""


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    mid = len(ordered) // 2
    return ordered[mid] if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2


def partition_and_check_health(location: str) -> dict:
    """Partitioned assets with failed or missing partitions, and assets that have no asset checks."""
    nodes = [n for n in _gql(HEALTH_QUERY, {})["assetNodes"] if n["repository"]["location"]["name"] == location]
    partitions = []
    for n in nodes:
        stats = n["partitionStats"]
        if not stats:
            continue
        missing = stats["numPartitions"] - stats["numMaterialized"] - stats["numFailed"] - stats["numMaterializing"]
        if stats["numFailed"] or missing:
            partitions.append(
                {"asset_key": n["assetKey"]["path"], "partitions": stats["numPartitions"],
                 "materialized": stats["numMaterialized"], "failed": stats["numFailed"], "missing": missing}
            )
    return {
        "partitions_needing_attention": partitions,
        "assets_without_checks": [n["assetKey"]["path"] for n in nodes if not n["hasAssetChecks"]],
        "assets_with_checks": [n["assetKey"]["path"] for n in nodes if n["hasAssetChecks"]],
    }


def runtime_changes(days: int = 14) -> dict:
    """Runs of the same asset selection that got slower: the recent half against the earlier half."""
    runs = _gql(HEALTH_QUERY, {})["runsOrError"]["results"]
    cutoff = time.time() - days * 86400
    groups: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for r in runs:
        if (
            not _in_location(r)
            or r["status"] != "SUCCESS"
            or not r["startTime"]
            or not r["endTime"]
            or r["startTime"] < cutoff
        ):
            continue
        key = ", ".join(sorted("/".join(a["path"]) for a in (r["assetSelection"] or []))) or r["pipelineName"]
        groups[key].append((r["startTime"], r["endTime"] - r["startTime"]))
    slower = []
    for key, rows in groups.items():
        rows.sort()
        if len(rows) < 4:
            continue
        half = len(rows) // 2
        before, after = _median([d for _, d in rows[:half]]), _median([d for _, d in rows[half:]])
        if after >= before * 1.5 and after - before >= 30:
            slower.append({"runs_of": key, "median_seconds_before": round(before), "median_seconds_after": round(after)})
    return {"window_days": days, "runs_considered": sum(len(v) for v in groups.values()), "slower": slower}


def dependency_report(running_libraries: list[dict] | None = None) -> dict:
    """How the project's dependencies are pinned, whether a lock file exists, and known vulnerabilities."""
    import tomllib

    from hooli_agents import github_scope

    tree = github_scope._call("GET", f"/git/trees/{github_scope.BASE_BRANCH}", params={"recursive": "1"})["tree"]
    names = {t["path"] for t in tree if not github_scope.is_excluded(t["path"])}
    lockfiles = sorted(n for n in names if n.split("/")[-1] in ("uv.lock", "poetry.lock", "Pipfile.lock", "requirements.txt"))
    deps = []
    with contextlib.suppress(github_scope.ScopeError):
        project = tomllib.loads(github_scope.read_file("pyproject.toml")).get("project", {})
        for spec in project.get("dependencies", []):
            name = re.split(r"[<>=!~\[ ;]", spec, maxsplit=1)[0]
            kind = "pinned" if "==" in spec else "range" if re.search(r"[<>~]", spec) else "unconstrained"
            deps.append({"name": name, "spec": spec, "kind": kind})
    vulnerable = []
    for lib in (running_libraries or [])[:25]:
        try:
            resp = requests.post(
                "https://api.osv.dev/v1/query",
                json={"package": {"name": lib["name"], "ecosystem": "PyPI"}, "version": lib["version"]},
                timeout=15,
            ).json()
        except requests.RequestException:
            continue
        ids = [v["id"] for v in resp.get("vulns", [])][:5]
        if ids:
            vulnerable.append({"package": lib["name"], "running_version": lib["version"], "advisories": ids})
    return {
        "declared_dependencies": deps,
        "lock_files": lockfiles,
        "has_lock_file": bool(lockfiles),
        "running_packages_checked_against_osv": len((running_libraries or [])[:25]),
        "running_packages_with_known_vulnerabilities": vulnerable,
    }


def incidents_last_24h(max_runs: int = 8) -> dict:
    """Runs that failed in the last 24 hours: job, assets, the error, and whether the same step keeps failing."""
    runs = _gql(HEALTH_QUERY, {})["runsOrError"]["results"]
    cutoff = time.time() - 86400
    failed = [
        r for r in runs if _in_location(r) and r["status"] == "FAILURE" and (r["startTime"] or 0) >= cutoff
    ][:max_runs]
    base = (settings.get("dagster_url") or "").rstrip("/")
    out = []
    for r in failed:
        events = _gql(
            "query($id:ID!){ logsForRun(runId:$id){ ... on EventConnection { events { __typename "
            "... on ExecutionStepFailureEvent { stepKey error { message cause { message } causes { message } } } } } } }",
            {"id": r["runId"]},
        )["logsForRun"]["events"]
        step_error = next(
            (
                (e["stepKey"], ((e["error"].get("causes") or [e["error"].get("cause") or e["error"]])[-1] or {}).get("message", "").strip().splitlines()[-1][:200])
                for e in events
                if e["__typename"] == "ExecutionStepFailureEvent" and e["error"]
            ),
            (None, ""),
        )
        out.append(
            {"run": f"{base}/runs/{r['runId']}", "job": r["pipelineName"],
             "assets": ["/".join(a["path"]) for a in (r["assetSelection"] or [])],
             "failed_step": step_error[0], "error": step_error[1]}
        )
    return {"failed_runs": len(failed), "incidents": out}
