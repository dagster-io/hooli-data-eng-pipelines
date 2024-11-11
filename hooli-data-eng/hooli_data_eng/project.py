import os
from dagster_dbt import DbtProject
from pathlib import Path


def get_env():
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "data-eng-prod":
        return "PROD"
    if os.getenv("DAGSTER_IS_DEV_CLI"):
        return "LOCAL"
    # default to BRANCH so we use that in github CI
    return "BRANCH"


dbt_project_path = Path(__file__).parent.parent.parent.joinpath("dbt_project")
DBT_PROJECT_DIR = os.fspath(dbt_project_path)

dbt_project = DbtProject(
    project_dir=dbt_project_path,
    state_path="target/slim_ci",
    target=get_env(),
)
dbt_project.prepare_if_dev()
