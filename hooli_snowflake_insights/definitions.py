import os

from dagster import Definitions, EnvVar, ResourceDefinition
from dagster_cloud.dagster_insights import (
    create_snowflake_insights_asset_and_schedule,
)
from dagster_snowflake import SnowflakeResource

# Used to derive environment (LOCAL, BRANCH, PROD)
def get_env():
    if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "") == "1":
        return "BRANCH"
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "data-eng-prod":
        return "PROD"
    return "LOCAL"

# Setting connection details by environment
resource_def = {
    "LOCAL": {
        "snowflake_insights": ResourceDefinition.none_resource(),
    },
    "BRANCH": {
        "snowflake_insights": SnowflakeResource(
            account=EnvVar("SNOWFLAKE_ACCOUNT"),
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
        ),
    },
    "PROD": {
        "snowflake_insights": SnowflakeResource(
            account=EnvVar("SNOWFLAKE_ACCOUNT"),
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
        ),
    },
}

# Creates an asset (poll_snowflake_query_history_hour) and sets its schedule
snowflake_insights_definitions = create_snowflake_insights_asset_and_schedule(
    "2023-10-29-00:00",
    snowflake_resource_key="snowflake_insights",
    snowflake_usage_latency=200
)

defs = Definitions(
    assets=[*snowflake_insights_definitions.assets,],
    schedules=[snowflake_insights_definitions.schedule,],
    resources=resource_def[get_env()],
)