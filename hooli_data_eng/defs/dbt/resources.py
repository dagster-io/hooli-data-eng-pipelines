import os
from pathlib import Path
from dagster_dbt import DbtProject, DbtCliResource
from hooli_data_eng.utils import get_env


dbt_project_path = Path(__file__).parent.parent.parent.parent.joinpath("dbt_project")
DBT_PROJECT_DIR = os.fspath(dbt_project_path)

dbt_project = DbtProject(
    project_dir=dbt_project_path,
    state_path="target/slim_ci",
    target=get_env(),
)
dbt_project.prepare_if_dev()


# The dbt file dbt_project/config/profiles.yaml
# specifies what databases to targets, and locally will
# execute against a DuckDB

# Similar to having different dbt targets, here we create the resource
# configuration by environment

resource_def = {
    "LOCAL": {
        "dbt": DbtCliResource(project_dir=dbt_project, target="LOCAL"),
    },
    "BRANCH": {
        "dbt": DbtCliResource(project_dir=dbt_project, target="BRANCH"),
    },
    "PROD": {
        "dbt": DbtCliResource(project_dir=dbt_project, target="PROD"),
    },
}
