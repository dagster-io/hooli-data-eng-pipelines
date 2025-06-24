from dagster_duckdb import DuckDBResource
from dagster_snowflake import SnowflakeResource
import os
import dagster as dg


# added for duckdb local, snowflake on branch or prod
def get_env():
    if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "") == "1":
        return "BRANCH"
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "data-eng-prod":
        return "PROD"
    return "LOCAL"

# Setting connection details by environment
resource_def = {
    "LOCAL": {
        # made generic
        "database_resource": DuckDBResource(database="/tmp/jaffle_platform.duckdb"),
    },
    "BRANCH": {
        "database_resource": SnowflakeResource(
            database="DEMO_DB2_BRANCH",
            account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
            user=dg.EnvVar("SNOWFLAKE_USER"),
            password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
            warehouse="TINY_WAREHOUSE",
        ),
    },
    "PROD": {
        "database_resource": SnowflakeResource(
            database="DEMO_DB2_BRANCH",
            account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
            user=dg.EnvVar("SNOWFLAKE_USER"),
            password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
            warehouse="TINY_WAREHOUSE",
        ),
    },
}


@dg.definitions
def resources():
    return dg.Definitions(
        resources=resource_def[get_env()]
    )

