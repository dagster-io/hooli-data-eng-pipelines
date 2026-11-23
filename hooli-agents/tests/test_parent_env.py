import os

from hooli_agents import _parent_env


def test_copies_prefixed_variables_without_overriding(tmp_path, monkeypatch):
    environ = tmp_path / "environ"
    environ.write_bytes(
        b"ENG_REPO=a/b\0DAGSTER_PLUS_ORG=hooli\0ENG_KEEP=parent\0OPENAI_API_KEY=x\0PATH=/bin\0"
    )
    for name in ("ENG_REPO", "DAGSTER_PLUS_ORG", "OPENAI_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("ENG_KEEP", "own")
    copied = _parent_env.load(environ)
    assert sorted(copied) == ["DAGSTER_PLUS_ORG", "ENG_REPO"]
    assert os.environ["ENG_REPO"] == "a/b"
    assert os.environ["ENG_KEEP"] == "own"
    assert "OPENAI_API_KEY" not in os.environ


def test_missing_parent_environment_is_ignored(tmp_path):
    assert _parent_env.load(tmp_path / "nope") == []
