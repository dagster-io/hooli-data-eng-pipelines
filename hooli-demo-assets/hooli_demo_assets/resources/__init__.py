import os

from dagster import EnvVar
from pathlib import Path
from dagster_embedded_elt.sling import (
    SlingResource,
    SlingSourceConnection,
    SlingTargetConnection,
)

def get_env():
    if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "") == "1":
        return "BRANCH"
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "data-eng-prod":
        return "PROD"
    return "LOCAL"

# embedded elt source and target
current_file_path = Path(__file__)
parent_dir_path = current_file_path.parent.parent.parent.parent
DUCKDB_PATH = parent_dir_path / "dbt_project" / "example.duckdb"

source = SlingSourceConnection(
        type="s3",
        bucket=EnvVar("AWS_S3_BUCKET"),
        region=EnvVar("AWS_REGION"),
        access_key_id=EnvVar("AWS_ACCESS_KEY_ID"),
        secret_access_key=EnvVar("AWS_SECRET_ACCESS_KEY"),
)
local_target = SlingTargetConnection(
        type="duckdb",
        instance=f"{DUCKDB_PATH}",
)
branch_target = SlingTargetConnection(
        type="snowflake",
        host=EnvVar("SNOWFLAKE_HOST"),
        database="DEMO_DB2_BRANCH",
        user=EnvVar("SNOWFLAKE_USER"),
        password=EnvVar("SNOWFLAKE_PASSWORD"),
        role=EnvVar("SNOWFLAKE_ROLE"),
)
prod_target = SlingTargetConnection(
        type="snowflake",
        host=EnvVar("SNOWFLAKE_HOST"),
        database="DEMO_DB2",
        user=EnvVar("SNOWFLAKE_USER"),
        password=EnvVar("SNOWFLAKE_PASSWORD"),
        role=EnvVar("SNOWFLAKE_ROLE"),
)

resource_def = {
    "LOCAL": {
         "s3_to_snowflake_resource":
         SlingResource(source_connection=source, target_connection=local_target),
    },
    "BRANCH": {
         "s3_to_snowflake_resource": SlingResource(
            source_connection=source, target_connection=branch_target
        ),
    },
    "PROD": {
        "s3_to_snowflake_resource": SlingResource(
            source_connection=source, target_connection=prod_target
        ),
    },
}