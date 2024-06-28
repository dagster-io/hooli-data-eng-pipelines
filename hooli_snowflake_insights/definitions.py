import os

from dagster import Definitions, EnvVar, ResourceDefinition,asset, AssetExecutionContext
from dagster_cloud.dagster_insights import (
    create_snowflake_insights_asset_and_schedule,
)
from dagster_snowflake import SnowflakeResource
from contextlib import closing

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


def execute_snowflake_queries(context, snowflake: SnowflakeResource, queries: list):
    with snowflake.get_connection() as conn:
        with closing(conn.cursor()) as cursor:
            for query in queries:
                cursor.execute(query)
                context.log.info("Executing query: " + query)


@asset
def test_execute_queries_with_get_connection(context: AssetExecutionContext, snowflake_insights: SnowflakeResource):
    queries = [
        "select 1",
        "select 2"
    ]
    execute_snowflake_queries(context, snowflake_insights, queries)

@asset
def test_execute_queries(snowflake_insights: SnowflakeResource):
    queries = [
        "select 1",
        "select 2"
    ]
    snowflake_insights.execute_queries(sql_queries=queries, fetch_results=False)

# Creates an asset (poll_snowflake_query_history_hour) and sets its schedule
snowflake_insights_definitions = create_snowflake_insights_asset_and_schedule(
    "2023-10-29-00:00",
    snowflake_resource_key="snowflake_insights",
    snowflake_usage_latency=45
)

defs = Definitions(
    assets=[*snowflake_insights_definitions.assets,test_execute_queries, test_execute_queries_with_get_connection],
    schedules=[snowflake_insights_definitions.schedule,],
    resources=resource_def[get_env()],
)
