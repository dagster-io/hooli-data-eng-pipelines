"""Linear access limited to one team, with only find and create. The API key comes from a private file."""

import re
from pathlib import Path

import requests

from hooli_agents import ledger, settings

API = "https://api.linear.app/graphql"
LABEL = "engineering-agent"
MARKER = "Filed by an engineering agent."


class LinearError(Exception):
    pass


def _key() -> str:
    path = settings.get("linear_api_key_file")
    if not path or not Path(path).exists():
        raise LinearError("Set linear_api_key_file (ENG_LINEAR_API_KEY_FILE) to a file holding a Linear API key.")
    return Path(path).read_text().strip()


def _team() -> str:
    team = settings.get("linear_team_id")
    if not team:
        raise LinearError("Set linear_team_id (ENG_LINEAR_TEAM_ID): the one team tickets are filed in.")
    return team


def _gql(query: str, variables: dict | None = None) -> dict:
    resp = requests.post(
        API,
        json={"query": query, "variables": variables or {}},
        headers={"Authorization": _key(), "Content-Type": "application/json"},
        timeout=30,
    )
    data = resp.json()
    if resp.status_code >= 400 or data.get("errors"):
        raise LinearError(f"Linear request failed: {str(data.get('errors') or data)[:300]}")
    return data["data"]


def _label_id(team: str) -> str | None:
    """The team's engineering-agent label, created if allowed; None when the key may not create labels."""
    labels = _gql(
        "query($t:String!){ team(id:$t){ labels(first:100){ nodes{ id name } } } }", {"t": team}
    )["team"]["labels"]["nodes"]
    for lab in labels:
        if lab["name"] == LABEL:
            return lab["id"]
    try:
        made = _gql(
            "mutation($i:IssueLabelCreateInput!){ issueLabelCreate(input:$i){ issueLabel{ id } } }",
            {"i": {"name": LABEL, "teamId": team, "color": "#1d76db"}},
        )
    except LinearError:
        return None
    return made["issueLabelCreate"]["issueLabel"]["id"]


def find_issues(query: str) -> list[dict]:
    """Open tickets the agents filed in the team whose title has any of the query's main words."""
    generic = {"dagster", "assets", "asset", "project", "improve", "improvements", "reliability"}
    words = [w for w in dict.fromkeys(re.findall(r"[A-Za-z0-9]{5,}", query.lower())) if w not in generic][:6]
    if not words:
        return []
    data = _gql(
        """query($t:ID!,$f:[IssueFilter!]!){ issues(first:20, filter:{ team:{id:{eq:$t}},
        description:{contains:"Filed by an engineering agent."}, state:{type:{nin:["completed","canceled"]}},
        or:$f }){ nodes{ identifier title url } } }""",
        {"t": _team(), "f": [{"title": {"containsIgnoreCase": w}} for w in words]},
    )
    return data["issues"]["nodes"]


def create_issue(title: str, body: str) -> dict:
    if settings.shadow():
        ledger.record("would_file", place="linear_ticket", title=title, body=body[:1500])
        return {"practice_mode": True, "would_open": "linear_ticket", "title": title, "url": "(practice mode: nothing was filed)"}
    team = _team()
    label = _label_id(team)
    issue_input = {"teamId": team, "title": title, "description": f"{body}\n\n---\n{MARKER}"}
    if label:
        issue_input["labelIds"] = [label]
    data = _gql(
        "mutation($i:IssueCreateInput!){ issueCreate(input:$i){ success issue{ identifier title url } } }",
        {"i": issue_input},
    )
    issue = data["issueCreate"]["issue"]
    ledger.record("linear_ticket", title=title, url=issue["url"], number=issue["identifier"])
    return issue


def list_agent_issues() -> list[dict]:
    data = _gql(
        """query($t:ID!){ issues(first:50, filter:{ team:{id:{eq:$t}}, description:{contains:"Filed by an engineering agent."},
        state:{type:{nin:["completed","canceled"]}} }){ nodes{ identifier title url description } } }""",
        {"t": _team()},
    )
    return [
        {"number": i["identifier"], "title": i["title"], "url": i["url"], "body": i.get("description") or ""}
        for i in data["issues"]["nodes"]
    ]
