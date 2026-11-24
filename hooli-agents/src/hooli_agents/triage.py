"""Decide which failed runs are worth analyzing: skip repeats of one failure, and retries of an analyzed run."""

import hashlib
import re
from datetime import datetime, timedelta, timezone

import dagster as dg

JOB = "bug_fix_job"
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)
_PATH = re.compile(r"(?:/[\w.\-<>]+){2,}")
_HEX = re.compile(r"\b[0-9a-f]{8,}\b", re.IGNORECASE)
_NUMBER = re.compile(r"\d+")
_DYNAMIC_KEY = re.compile(r"\[[^\]]*\]")


def normalize_message(text: str) -> str:
    """First line of an error with ids, paths and numbers removed, so one cause gives one text."""
    line = (text or "").strip().splitlines()[0] if (text or "").strip() else ""
    for pattern, token in ((_UUID, "<id>"), (_PATH, "<path>"), (_HEX, "<id>"), (_NUMBER, "<n>")):
        line = pattern.sub(token, line)
    return re.sub(r"\s+", " ", line).lower()[:200]


def error_leaf(error) -> tuple[str, str]:
    """Class name and message of the innermost cause of a serialized error."""
    while getattr(error, "cause", None) is not None:
        error = error.cause
    return getattr(error, "cls_name", "") or "", getattr(error, "message", "") or ""


def signature(location: str, job: str, step_keys: list[str], error_cls: str, message: str) -> str:
    steps = sorted({_DYNAMIC_KEY.sub("", key) for key in step_keys})
    raw = "|".join([location, job, ",".join(steps), error_cls, normalize_message(message)])
    return hashlib.sha1(raw.encode()).hexdigest()[:12]


def failure_signature(context: dg.RunFailureSensorContext, location: str) -> str:
    """The same signature for the same failure: same job, step (without dynamic suffix) and error cause."""
    run = context.dagster_run
    steps: list[str] = []
    error_cls, message = "", ""
    for event in context.get_step_failure_events():
        if event.step_key:
            steps.append(event.step_key)
        data = event.step_failure_data
        if data and data.error and not message:
            error_cls, message = error_leaf(data.error)
    if not message:
        message = getattr(context.failure_event, "message", "") or ""
    return signature(location, run.job_name, steps, error_cls, message)


def _since(hours: float) -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=hours)


def analyzed_recently(instance: dg.DagsterInstance, sig: str, hours: float) -> bool:
    runs = instance.get_runs(
        filters=dg.RunsFilter(job_name=JOB, tags={"eng/signature": sig}, created_after=_since(hours)), limit=1
    )
    return bool(runs)


def analyzed_run(instance: dg.DagsterInstance, run_id: str) -> bool:
    return bool(instance.get_runs(filters=dg.RunsFilter(job_name=JOB, tags={"eng/failed_run_id": run_id}), limit=1))


def analyses_since(instance: dg.DagsterInstance, hours: float = 24) -> int:
    return instance.get_runs_count(filters=dg.RunsFilter(job_name=JOB, created_after=_since(hours)))
