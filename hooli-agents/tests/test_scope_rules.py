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


def test_agents_never_watch_their_own_location(monkeypatch):
    monkeypatch.setenv("ENG_WATCHED_LOCATION", "")
    assert not ops_tools.location_watched("hooli_agents")


def test_agents_ignore_pull_requests_on_other_branches(monkeypatch):
    prs = [{"number": 1, "head": {"ref": "agent/fix", "sha": "a" * 40}, "title": "t", "html_url": "u", "user": {"login": "x"}},
           {"number": 2, "head": {"ref": "feature/other", "sha": "b" * 40}, "title": "t", "html_url": "u", "user": {"login": "y"}}]
    monkeypatch.setattr(gh, "_call", lambda method, path, **kw: prs if path == "/pulls" else prs[1])
    assert [p["number"] for p in gh.open_pull_requests()] == [1]
    try:
        gh.get_pull_request(2)
        raise AssertionError("expected ScopeError")
    except gh.ScopeError as e:
        assert "agent branch" in str(e)


def test_advisor_location_setting(monkeypatch):
    monkeypatch.setenv("ENG_WATCHED_LOCATION", "")
    monkeypatch.setenv("ENG_ADVISOR_LOCATION", "basics")
    monkeypatch.setattr(ops_tools, "_gql", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("reached graphql")))
    try:
        ops_tools.project_overview()
    except RuntimeError as e:
        assert "reached graphql" in str(e)
