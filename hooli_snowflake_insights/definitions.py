from dagster import Definitions, EnvVar
from dagster_cloud.dagster_insights import (
    create_snowflake_insights_asset_and_schedule,
)
from dagster_snowflake import SnowflakeResource

# Creates an asset (poll_snowflake_query_history_hour) and sets its schedule
snowflake_insights_definitions = create_snowflake_insights_asset_and_schedule(
    "2023-10-29-00:00",
    snowflake_resource_key="snowflake_insights",
)

defs = Definitions(
    assets=[*snowflake_insights_definitions.assets,],
    schedules=[snowflake_insights_definitions.schedule,],
    resources={
        "snowflake_insights": SnowflakeResource(
            account=EnvVar("SNOWFLAKE_ACCOUNT"),
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
    )
 }
)