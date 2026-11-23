"""MCP server (stdio) exposing the repo-scoped GitHub tools to the engineering agents."""

from fastmcp import FastMCP

from hooli_agents import _parent_env

_parent_env.load()  # must run before the modules below read their settings

from hooli_agents import github_scope as gh  # noqa: E402
from hooli_agents import ledger, ops_tools  # noqa: E402
from hooli_agents import linear_scope as lin  # noqa: E402

mcp = FastMCP("engineering-repo")


def _guard(fn):
    def run(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (gh.ScopeError, lin.LinearError) as e:
            ledger.record("refused", tool=fn.__name__, reason=str(e)[:300])
            return {"error": str(e)}

    run.__name__ = fn.__name__
    run.__doc__ = fn.__doc__
    return run


@mcp.tool
def list_files(path: str = "") -> list | dict:
    """List files in the repository's main branch under a folder ('' for the root)."""
    return _guard(gh.list_files)(path)


@mcp.tool
def read_file(path: str, ref: str = gh.BASE_BRANCH) -> str | dict:
    """Read one file from the repository (main branch unless a branch is given)."""
    return _guard(gh.read_file)(path, ref)


@mcp.tool
def propose_fix(branch: str, title: str, body: str, files: list[dict], note: str = "") -> dict:
    """Open a pull request that changes files. `files` is a list where each item is either
    {path, old, new}, which replaces that exact text (it must appear once) and leaves the rest of the file
    untouched, or {path, content} with the FULL new content (only for new files). The branch is created for you under agent/. CI, dependencies and packaging
    files are protected. Never merges."""
    return _guard(gh.propose_fix)(branch, title, body, files, note)


@mcp.tool
def propose_improvement(branch: str, title: str, body: str, files: list[dict]) -> dict:
    """Open a pull request for an improvement that changes behavior (retry policy, freshness, automation).
    `files` items are {path, old, new} (replace exact text that appears once; preferred, it keeps the
    formatting of the rest of the file) or {path, content} (new files only). Same limits as propose_fix,
    and it always needs a person's approval. Never merges."""
    return _guard(gh.propose_fix)(branch, title, body, files, "", "improvement")


@mcp.tool
def list_open_pull_requests() -> list | dict:
    """Open pull requests (number, title, branch author), to avoid proposing a change twice."""
    return _guard(gh.open_pull_requests)()


@mcp.tool
def find_issues(query: str) -> list | dict:
    """Open issues the agents already filed that match some words, to avoid filing a finding twice."""
    return _guard(gh.find_issues)(query)


@mcp.tool
def open_issue(title: str, body: str, labels: list[str] | None = None) -> dict:
    """File an issue with the finding and the analysis. Use it for findings that are not a code change
    you can make, or when a person should decide first. Check find_issues first."""
    return _guard(gh.open_issue)(title, body, labels)


@mcp.tool
def linear_find_issues(query: str) -> list | dict:
    """Open Linear tickets the agents already filed whose title contains the words, to avoid duplicates."""
    return _guard(lin.find_issues)(query)


@mcp.tool
def linear_create_issue(title: str, body: str) -> dict:
    """File a Linear ticket in the configured team with the finding and the analysis in the body.
    Check linear_find_issues first. Returns the identifier and the URL to link."""
    return _guard(lin.create_issue)(title, body)


@mcp.tool
def retry_report(days: int = 7) -> dict:
    """Steps that retried in recent runs: how often, the errors, and whether the run still succeeded."""
    return ops_tools.retry_report(days)


@mcp.tool
def check_dagster_api(names: list[str]) -> dict:
    """Check that Dagster names exist in the installed version and get their signatures, for example
    ["dg.AutomationCondition.eager", "dg.FreshnessPolicy.time_window"]. Call it for every Dagster name
    you put in a code snippet; if a name does not exist, use one that does."""
    return ops_tools.check_dagster_api(names)


@mcp.tool
def deprecation_report() -> dict:
    """Removed, deprecated or superseded Dagster APIs the repository's code uses, with file, line,
    the version where they break and the replacement hint. Call it once."""
    return ops_tools.deprecation_report()


@mcp.tool
def list_locations() -> dict:
    """The code locations to review. Call it first, then project_overview once for each."""
    return ops_tools.list_locations()


@mcp.tool
def project_overview(location: str = "") -> dict:
    """Facts about one code location under review (default: the first watched one): each asset with its freshness policy, automation condition
    and the schedules that run it; all schedules; alert policies; the Dagster dependency and the newest
    release. Call it once first."""
    return ops_tools.project_overview(location)


@mcp.tool
def latest_dagster_release() -> dict:
    """The newest Dagster release with its notes."""
    return ops_tools.latest_dagster_release()


@mcp.tool
def get_pull_request(number: int) -> dict:
    """A pull request's title, description, changed files with patches, and CI check state."""
    return _guard(gh.get_pull_request)(number)


@mcp.tool
def assess_pull_request(number: int) -> dict:
    """The fixed risk assessment for a PR: level 'low' or 'needs_human', and the reasons."""

    def go(n):
        return gh.assess_risk(gh.get_pull_request(n))

    return _guard(go)(number)


@mcp.tool
def review_pull_request(number: int, decision: str, body: str) -> dict:
    """Review a PR. decision is COMMENT or APPROVE. APPROVE is refused unless the PR is low risk."""
    return _guard(gh.review_pull_request)(number, decision, body)


if __name__ == "__main__":
    mcp.run()
