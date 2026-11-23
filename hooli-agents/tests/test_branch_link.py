from hooli_agents.github_scope import find_branch_deployment_url as find


def test_reads_the_link_from_the_action_comment():
    comment = (
        "Your pull request is automatically being deployed to Dagster Cloud.\n\n"
        "| Location | Status | Link |\n| `my_project` | Ready | "
        "[View in Cloud](https://acme.dagster.cloud/acme--pr-42/home) | \n"
        "Learn more in the [docs](https://docs.dagster.cloud/docs/branch-deployments)."
    )
    assert find([comment]) == "https://acme.dagster.cloud/acme--pr-42/home"


def test_prefers_a_deployment_link_over_a_generic_one():
    assert (
        find(["see https://acme.dagster.cloud/", "https://acme.dagster.cloud/branch-xyz/assets"])
        == "https://acme.dagster.cloud/branch-xyz/assets"
    )


def test_reads_a_check_details_url_and_trims_punctuation():
    assert find(["", "Deployed: https://acme.dagster.cloud/acme--feat-1."]) == (
        "https://acme.dagster.cloud/acme--feat-1"
    )


def test_none_when_the_action_is_not_installed():
    assert find(["Looks good to me", "", "https://github.com/x/y/actions/runs/1"]) is None
