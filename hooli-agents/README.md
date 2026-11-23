# Hooli agents

Three engineering agents built from Dagster community components. They run as their own code location (`hooli_agents`) in the same Dagster+ deployment as the pipelines they watch (`data-eng-prod`). A bad agent change only redeploys its own location; the other locations are untouched.

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

## What they watch, and what they change

- **Watched locations:** the failed-run sensor is a run failure sensor that monitors every code location in the deployment. `ENG_WATCHED_LOCATION` takes a comma-separated list; empty means all of them except `hooli_agents` itself, so a failing agent never starts the bug fixer. The advisor reviews every watched location, one overview per location, unless `ENG_ADVISOR_LOCATION` limits it to one.
- **Branch deployments:** the sensors do nothing there, so a PR does not double-post announcements.
- **Changed repository:** the agents change one repository only, set by `ENG_REPO`, on branch `ENG_BASE_BRANCH` (default `main`; this repo uses `master`). For the code that runs in `data-eng-prod` that is this repository, so set `ENG_AUTO_MERGE=false`: every merge here deploys to production, and a person should press it.
- **Protected files:** `.github/`, `pyproject.toml`, requirements, `uv.lock`, `Dockerfile`, `setup.*` and `dagster_cloud*` files are never changed by an agent, in any project folder. A change is low risk only if it is at most 2 files and 30 lines, under a `src`, `tests` or `docs` folder, and checks pass; the reviewer can approve only those.
- **Skill:** `bug_fixer` and `improvement_advisor` load the `dagster-expert` skill, fetched from `dagster-io/skills` (so the image needs `git` and network access) the first time an agent uses it.

## Setup

1. In Dagster+, set these as environment variables on `data-eng-prod`, scoped to the `hooli_agents` code location (secrets as secrets):

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | model key used by the agents (change `model` and `api_key_env_var` in the agent YAML to switch provider) |
| `SLACK_BOT_TOKEN` | posts announcements and reads reactions |
| `ENG_SLACK_CHANNEL` | channel id for announcements and approvals |
| `ENG_REPO` | `owner/name` of the target repository |
| `ENG_GITHUB_TOKEN` | token for the author identity (opens pull requests and issues) |
| `ENG_REVIEWER_GITHUB_TOKEN`, `ENG_REVIEWER_GH_USER` | a second GitHub login that approves, since GitHub does not let an author approve their own pull request |
| `ENG_DAGSTER_URL` | UI base URL, `https://hooli.dagster.cloud/data-eng-prod`, used for run links |
| `ENG_DAGSTER_GRAPHQL_URL`, `ENG_DAGSTER_API_TOKEN` | still needed by the advisor's evidence tool (assets, schedules, alerts, running versions) and by the re-run after a merge; the failure sensor does not use them |
| `DAGSTER_PLUS_MCP_URL` | URL of the Dagster+ MCP server used by `bug_fixer` for run logs (`https://mcp.agent.dagster.cloud/mcp`) |
| `DAGSTER_PLUS_ORG`, `DAGSTER_PLUS_BEARER` | the MCP server's organization header (`hooli`) and authorization header (`Bearer <token>`) |
| `ENG_WATCHED_LOCATION` | code locations to watch (comma-separated; empty is all) |
| `ENG_ADVISOR_LOCATION` | optional; limit the improvement advisor to one code location (default: every watched location) |
| `ENG_BASE_BRANCH` | branch agent pull requests target (`master` for this repo) |
| `ENG_AUTO_MERGE` | `false` to leave every merge to a person |
| `ENG_VAR_DIR` | optional; where the ledger and sensor state are kept (defaults to the project `var/`, which is lost when the pod restarts) |
| `ENG_LINEAR_TEAM_ID`, `ENG_LINEAR_API_KEY_FILE` | optional; only for filing Linear tickets |

Other settings (`auto_merge`, `verify_after_merge`, `post_merge_command`) can be set the same way as `ENG_<NAME>`.

## Practice mode

Set `ENG_SHADOW=practice` and filing tools record what they would file and change nothing. Scope the variable to **branch deployments** in Dagster+: an agent change arrives as a pull request, its branch deployment runs the agents in practice mode, and merging promotes it to `data-eng-prod`, where the variable is unset. The value must be a word; a number-like value is stored as an integer and the location will not load.

## Develop

```
cd hooli-agents
uv sync --extra dev
DAGSTER_PLUS_MCP_URL=http://localhost/mcp ENG_REPO=example/example uv run dg check defs
uv run pytest tests
```

## Deployment

`hooli_agents` is a location in `dagster_cloud.yaml` and in `.github/workflows/deploy-dagster-cloud.yml`, built and deployed like the other locations when `hooli-agents/**` changes.

Run pods get 4G of memory and 1 CPU (`container_context` in `dagster_cloud.yaml`). A change to `dagster_cloud.yaml` redeploys this location, because the limits only apply when the location is redeployed.
