# Hooli agents

Three engineering agents built from Dagster community components, deployed as their own code location (`hooli_agents`) in their own Dagster+ deployment (`agents`), separate from `data-eng-prod`.

| Agent | Starts when | What it does |
|---|---|---|
| `bug_fixer` | a run fails in the watched code location | finds the cause in the code and opens a fix pull request |
| `pr_reviewer` | an agent pull request opens | scores risk in code; approves low-risk changes, asks a person (a Slack reaction) for the rest |
| `improvement_advisor` | on a schedule you set, or by hand | reads the deployment and files findings as pull requests, GitHub issues or Linear tickets |

Each agent writes an outcome asset (`status`, `summary`, `filed`, `would_file`, `refused`, `decisions_for_you`), and the advisor has an asset check that grades its findings against `eval/improvement_fixtures.json`.

## Layout

- `src/hooli_agents/defs/agents/*/defs.yaml`: the agents, their tool servers and Slack replies, as components.
- `src/hooli_agents/defs/triggers.py`: sensors that start the agents, and the approval watcher that merges after a person approves.
- `src/hooli_agents/*_scope.py`, `ops_tools.py`, `repo_mcp.py`: the tools the agents get, served over MCP (stdio). Risk rules, duplicate checks and API checks live here, not in prompts.
- `eval/`: fixtures for the grading asset check.

## Target repository

The agents change one repository only, set by `ENG_REPO`. **Do not point it at this repository.** Use a throwaway repo with a Dagster project in it. `CI`, dependency and packaging files are protected from agent edits.

## Setup

1. Create the deployment once: `dagster-cloud deployment create agents`.
2. Set these on the `agents` deployment (Dagster+ environment variables; secrets as secrets):

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | model key used by the agents (change `model` and `api_key_env_var` in the agent YAML to switch provider) |
| `SLACK_BOT_TOKEN` | posts announcements and reads reactions |
| `ENG_SLACK_CHANNEL` | channel id for announcements and approvals |
| `ENG_REPO` | `owner/name` of the target repository |
| `ENG_GITHUB_TOKEN` | token for the author identity (opens pull requests and issues) |
| `ENG_REVIEWER_GITHUB_TOKEN`, `ENG_REVIEWER_GH_USER` | a second GitHub login that approves, since GitHub does not let an author approve their own pull request |
| `ENG_DAGSTER_GRAPHQL_URL`, `ENG_DAGSTER_URL`, `ENG_DAGSTER_API_TOKEN` | Dagster+ GraphQL endpoint (`https://hooli.dagster.cloud/agents/graphql`), UI base URL, and an agent-scoped API token |
| `DAGSTER_PLUS_MCP_URL` | URL of the Dagster+ MCP server used by `bug_fixer` for run logs |
| `ENG_WATCHED_LOCATION` | code location whose failures start the bug fixer |
| `ENG_VAR_DIR` | optional; where the ledger and sensor state are kept (defaults to the project `var/`, which is lost when the pod restarts) |
| `ENG_LINEAR_TEAM_ID`, `ENG_LINEAR_API_KEY_FILE` | optional; only for filing Linear tickets |

Other settings (`auto_merge`, `verify_after_merge`, `post_merge_command`) can be set the same way as `ENG_<NAME>`.

## Practice mode

Set `ENG_SHADOW=practice` and filing tools record what they would file and change nothing. Scope the variable to **branch deployments** in Dagster+: an agent change arrives as a pull request, its branch deployment runs the agents in practice mode, and merging promotes it to `agents`, where the variable is unset. The value must be a word; a number-like value is stored as an integer and the location will not load.

## Develop

```
cd hooli-agents
uv sync --extra dev
DAGSTER_PLUS_MCP_URL=http://localhost/mcp ENG_REPO=example/example uv run dg check defs
uv run pytest tests
```

## Deployment

`.github/workflows/deploy-hooli-agents.yml` deploys on changes under `hooli-agents/` using `dagster_cloud_agents.yaml`. The existing `deploy-dagster-cloud.yml` is untouched and does not deploy this location.
