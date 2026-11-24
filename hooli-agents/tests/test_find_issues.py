from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from hooli_agents import github_scope as gh


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
