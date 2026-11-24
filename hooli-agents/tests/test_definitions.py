import dagster as dg
import pytest

from hooli_agents.definitions import defs

EXPECTED_SENSORS = {
    "failed_run_trigger",
    "new_pr_trigger",
    "pr_approval_watcher",
    "new_issue_announcer",
    "weekly_improvement_review",
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
