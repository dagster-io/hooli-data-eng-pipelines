import os
from pathlib import Path
from dagster_dbt import DbtProject, DbtCliResource
from hooli_data_eng.utils import get_env


dbt_project_path = Path(__file__).parent.parent.parent.parent.parent.joinpath("dbt_project")
DBT_PROJECT_DIR = os.fspath(dbt_project_path)

# Determine the root of the hooli-data-eng Dagster project
# resources.py is in hooli-data-eng/hooli_data_eng/defs/dbt/
# So, 4 levels up is the hooli-data-eng project directory
hooli_data_eng_project_root = Path(__file__).parent.parent.parent.parent
dbt_executable_on_host = hooli_data_eng_project_root.joinpath(".venv", "bin", "dbt").resolve()

# Add a check to ensure the dbt executable exists at the resolved path
if not dbt_executable_on_host.is_file():
    raise FileNotFoundError(
        f"dbt executable not found at expected path: {dbt_executable_on_host}. "
        "Ensure the virtual environment is correctly populated, the path is correct, "
        "and the file has execute permissions."
    )

dbt_executable_str = os.fspath(dbt_executable_on_host)

print(f"DBT Executable: {dbt_executable_str}")

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
        "dbt": DbtCliResource(
            project_dir=dbt_project, # Using the DbtProject instance is fine
            target="LOCAL",
            dbt_executable=dbt_executable_str, # Corrected argument name
        ),
    },
    "BRANCH": {
        "dbt": DbtCliResource(
            project_dir=dbt_project,
            target="BRANCH",
            dbt_executable=dbt_executable_str, # Corrected argument name
        ),
    },
    "PROD": {
        "dbt": DbtCliResource(
            project_dir=dbt_project,
            target="PROD",
            dbt_executable=dbt_executable_str, # Corrected argument name
        ),
    },
}
