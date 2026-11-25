import dagster as dg
import pytest

from hooli_agents.definitions import defs

EXPECTED_SENSORS = {
    "failed_run_trigger",
    "new_pr_trigger",
    "pr_approval_watcher",
    "new_issue_announcer",
    "weekly_improvement_review",
    "weekly_improvement_review_pipeline",
}


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    for name in ("ENG_GITHUB_TOKEN", "ENG_REVIEWER_GITHUB_TOKEN", "SLACK_BOT_TOKEN", "ENG_DAGSTER_API_TOKEN"):
        monkeypatch.setenv(name, "x")


def test_definitions_load_with_every_sensor_and_agent():
    loaded = defs() if callable(defs) else defs
    assert isinstance(loaded, dg.Definitions)
    assert EXPECTED_SENSORS <= {s.name for s in loaded.sensors}
    keys = {k.to_user_string() for a in loaded.assets for k in a.keys}
    assert {"bug_fixer", "pr_reviewer", "improvement_advisor"} <= keys


def test_advisor_pipeline_assets_and_outcome():
    loaded = defs() if callable(defs) else defs
    keys = {k.to_user_string() for a in loaded.assets for k in a.keys}
    assert {
        "improvement_advisor_pipeline_overviews",
        "improvement_advisor_pipeline_analysis",
        "improvement_advisor_pipeline_filed",
        "improvement_advisor_pipeline_outcome",
        "improvement_advisor_pipeline_reply",
    } <= keys


def test_advisor_pipeline_lineage_has_no_orphans():
    loaded = defs() if callable(defs) else defs
    graph = loaded.resolve_asset_graph()
    prefix = "improvement_advisor_pipeline_"
    parents = {
        key.to_user_string().removeprefix(prefix): {p.to_user_string().removeprefix(prefix) for p in graph.get(key).parent_keys}
        for key in graph.get_all_asset_keys()
        if key.to_user_string().startswith(prefix)
    }
    assert parents["analysis"] >= {"overviews", "deprecations"}
    assert parents["verified"] >= {"overviews", "deprecations"}
    roots = {name for name, ps in parents.items() if not ps}
    assert roots == {"locations", "deprecations"}
