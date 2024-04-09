import os
from dagster_dbt import DbtProject
from dagster._utils import file_relative_path


def get_env():
    if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "") == "1":
        return "BRANCH"
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "data-eng-prod":
        return "PROD"
    return "LOCAL"


DBT_PROJECT_DIR = file_relative_path(__file__, "../dbt_project")

dbt_project = DbtProject(
    project_dir=DBT_PROJECT_DIR,
    state_path="target/slim_ci",
    target=get_env(),
)
