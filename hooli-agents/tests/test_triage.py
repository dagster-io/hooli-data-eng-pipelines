from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import dagster as dg
from dagster._core.storage.dagster_run import DagsterRun

from hooli_agents import github_scope as gh
from hooli_agents import triage


def test_same_failure_gives_the_same_signature_across_runs_and_dynamic_steps():
    first = triage.signature(
        "batch_enrichment", "run_etl_pipeline", ["enriched_data.process_chunk[4]"], "builtins.Exception", "API time out"
    )
    second = triage.signature(
        "batch_enrichment", "run_etl_pipeline", ["enriched_data.process_chunk[9]"], "builtins.Exception", "API time out"
    )
    assert first == second


def test_different_causes_or_jobs_give_different_signatures():
    base = triage.signature("loc", "job", ["step"], "builtins.Exception", "API time out")
    assert base != triage.signature("loc", "job", ["step"], "builtins.KeyError", "'discount'")
    assert base != triage.signature("loc", "other_job", ["step"], "builtins.Exception", "API time out")
    assert base != triage.signature("loc", "job", ["other_step"], "builtins.Exception", "API time out")


def test_ids_paths_and_numbers_are_removed_from_messages():
    a = "FileNotFoundError: [Errno 2] No such file: '/opt/dagster/storage/eedfd34b-907b-43ed-98b6-bcdde48bedbc/x/result/4'"
    b = "FileNotFoundError: [Errno 2] No such file: '/opt/dagster/storage/c80b58fd-caec-433b-9da3-5dc317887cc5/x/result/9'"
    assert triage.normalize_message(a) == triage.normalize_message(b)


def test_error_leaf_follows_the_cause_chain():
    leaf = SimpleNamespace(cls_name="builtins.Exception", message="API time out", cause=None)
    wrapper = SimpleNamespace(cls_name="DagsterExecutionStepExecutionError", message="Error occurred", cause=leaf)
    assert triage.error_leaf(wrapper) == ("builtins.Exception", "API time out")


def test_recent_analyses_are_found_by_signature_and_counted():
    instance = dg.DagsterInstance.ephemeral()
    instance.add_run(DagsterRun(job_name=triage.JOB, run_id="r1", tags={"eng/signature": "abc", "eng/failed_run_id": "f1"}))
    assert triage.analyzed_recently(instance, "abc", 24)
    assert not triage.analyzed_recently(instance, "other", 24)
    assert triage.analyzed_run(instance, "f1")
    assert not triage.analyzed_run(instance, "f2")
    assert triage.analyses_since(instance, 24) == 1


def _issue(number, state, closed_days_ago=None):
    closed = (datetime.now(timezone.utc) - timedelta(days=closed_days_ago)).isoformat() if closed_days_ago is not None else None
    return {"number": number, "title": f"t{number}", "html_url": f"u{number}", "state": state, "closed_at": closed}


def test_find_issues_includes_recently_closed_but_not_old_closed(monkeypatch):
    items = [_issue(1, "open"), _issue(2, "closed", 3), _issue(3, "closed", 90)]
    monkeypatch.setattr(gh, "_token", lambda user: "x")
    monkeypatch.setattr(
        gh.requests, "get", lambda *a, **k: SimpleNamespace(status_code=200, json=lambda: {"items": items})
    )
    assert sorted(i["number"] for i in gh.find_issues("retries flaky")) == [1, 2]


def _failed_run_context(message: str, instance=None):
    @dg.op
    def process_chunk():
        raise Exception(message)

    @dg.job
    def run_etl_pipeline():
        process_chunk()

    instance = instance or dg.DagsterInstance.ephemeral()
    result = run_etl_pipeline.execute_in_process(instance=instance, raise_on_error=False)
    return dg.build_run_status_sensor_context(
        sensor_name="failed_run_trigger",
        dagster_instance=instance,
        dagster_run=result.dagster_run,
        dagster_event=result.get_run_failure_event(),
    ).for_run_failure()


def test_failure_signature_from_a_real_failed_run_ignores_run_ids():
    first = triage.failure_signature(_failed_run_context("API time out"), "batch_enrichment")
    second = triage.failure_signature(_failed_run_context("API time out"), "batch_enrichment")
    other = triage.failure_signature(_failed_run_context("missing field discount"), "batch_enrichment")
    assert first == second != other
