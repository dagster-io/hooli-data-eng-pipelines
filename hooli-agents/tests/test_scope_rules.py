from hooli_agents import github_scope as gh
from hooli_agents import ops_tools


def test_protected_paths_in_monorepo_projects():
    assert gh.is_protected(".github/workflows/deploy.yml")
    assert gh.is_protected("hooli-basics/Dockerfile")
    assert gh.is_protected("hooli-data-eng/pyproject.toml")
    assert gh.is_protected("dagster_cloud.yaml")
    assert not gh.is_protected("hooli-basics/src/hooli_basics/definitions.py")


def test_low_risk_paths_in_monorepo_projects():
    assert gh.is_low_risk("hooli-basics/src/hooli_basics/definitions.py")
    assert gh.is_low_risk("hooli-basics/tests/test_assets.py")
    assert gh.is_low_risk("README.md")
    assert not gh.is_low_risk("dbt_project/models/orders.sql")


def test_watched_locations(monkeypatch):
    monkeypatch.setenv("ENG_WATCHED_LOCATION", "basics, hooli_bi")
    assert ops_tools.location_watched("hooli_bi")
    assert not ops_tools.location_watched("other")
    monkeypatch.setenv("ENG_WATCHED_LOCATION", "")
    assert ops_tools.location_watched("anything")
