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


def test_list_locations_respects_watch_list(monkeypatch):
    entries = {"workspaceOrError": {"locationEntries": [{"name": n, "loadStatus": "LOADED"} for n in ("basics", "hooli_bi", "hooli_agents")]}}
    monkeypatch.setattr(ops_tools, "_gql", lambda *a, **k: entries)
    monkeypatch.setenv("ENG_WATCHED_LOCATION", "")
    monkeypatch.setenv("ENG_ADVISOR_LOCATION", "")
    assert ops_tools.list_locations() == {"locations": ["basics", "hooli_bi"]}
    monkeypatch.setenv("ENG_ADVISOR_LOCATION", "hooli_bi")
    assert ops_tools.list_locations() == {"locations": ["hooli_bi"]}


def test_agents_own_code_is_excluded(monkeypatch):
    monkeypatch.delenv("ENG_EXCLUDE_PATHS", raising=False)
    assert gh.is_excluded("hooli-agents/src/hooli_agents/definitions.py")
    assert gh.is_excluded("hooli-agents")
    assert not gh.is_excluded("hooli-basics/src/hooli_basics/definitions.py")
    assert not gh.is_excluded("hooli-agents-other/x.py")
    try:
        gh._safe_path("hooli-agents/README.md")
        raise AssertionError("expected ScopeError")
    except gh.ScopeError:
        pass


def test_asset_code_paths_come_from_github_references():
    node = {"metadataEntries": [{"codeReferences": [
        {"url": "https://github.com/o/r/tree/aae00c422be501764520f96a7e553e77607373f9/hooli-data-eng/src/hooli_data_eng/defs/dbt/component.py#L209"},
        {"url": "https://github.com/o/r/tree/aae00c422be501764520f96a7e553e77607373f9/dbt_project/models/a.sql"},
        {"filePath": "/opt/x.py"},
    ]}]}
    assert ops_tools._code_paths(node) == [
        {"path": "hooli-data-eng/src/hooli_data_eng/defs/dbt/component.py", "line": 209},
        {"path": "dbt_project/models/a.sql", "line": 0},
    ]


def test_outcome_drafts_are_readable_markdown():
    from hooli_agents.defs import outcomes

    text = outcomes._drafts_markdown(
        [{"kind": "github_issue", "title": "Filed one", "url": "https://x/1"}],
        [{"kind": "would_file", "place": "github_issue", "title": "Draft one", "body": "Full body\n```python\nx = 1\n```"}],
    )
    assert "## Draft one" in text and "Full body" in text and "x = 1" in text
    assert "## Filed one" in text and "https://x/1" in text
    assert outcomes._drafts_markdown([], []) == "Nothing was filed or drafted."
