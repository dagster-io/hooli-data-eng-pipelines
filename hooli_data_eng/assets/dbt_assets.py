
from dagster._utils import file_relative_path
from dagster_dbt import load_assets_from_dbt_project
from dagster import DailyPartitionsDefinition, HourlyPartitionsDefinition

daily_partitions = DailyPartitionsDefinition(start_date="2023-04-01")

hourly_partitions = HourlyPartitionsDefinition(
    start_date="2023-04-01-00:00"
)

DBT_PROJECT_DIR = file_relative_path(__file__, "../../dbt_project")
DBT_PROFILES_DIR = file_relative_path(__file__, "../../dbt_project/config")


def dbt_metadata(context, node_info):
    return {
        "owner": "data@hooli.com",
        "name": node_info["name"],
        "partition_expr": "dt"
    }

def partition_key_to_vars(partition_key):
    return {"datetime_to_process": partition_key}

hourly_dbt_assets = load_assets_from_dbt_project(
    DBT_PROJECT_DIR,
    DBT_PROFILES_DIR,
    key_prefix=["ANALYTICS"],
    source_key_prefix="ANALYTICS",
    runtime_metadata_fn=dbt_metadata,
    partition_key_to_vars_fn=partition_key_to_vars,
    partitions_def=hourly_partitions,
    select="orders_augmented"
)

hourly_dbt_assets_orders = load_assets_from_dbt_project(
    DBT_PROJECT_DIR,
    DBT_PROFILES_DIR,
    key_prefix=["ANALYTICS"],
    runtime_metadata_fn=dbt_metadata,
    partition_key_to_vars_fn=partition_key_to_vars,
    partitions_def=hourly_partitions,
    select="orders_cleaned"
)

daily_dbt_assets = load_assets_from_dbt_project(
    DBT_PROJECT_DIR,
    DBT_PROFILES_DIR,
    key_prefix=["ANALYTICS"],
    source_key_prefix="ANALYTICS",
    runtime_metadata_fn=dbt_metadata,
    partition_key_to_vars_fn=partition_key_to_vars,
    partitions_def=daily_partitions,
    select="daily_order_summary order_stats"
)

dbt_views = load_assets_from_dbt_project(
    DBT_PROJECT_DIR,
    DBT_PROFILES_DIR,
    key_prefix=["ANALYTICS"],
    source_key_prefix="ANALYTICS",
    runtime_metadata_fn=dbt_metadata,
    select="company_perf sku_stats company_stats"
)

dbt_views_users = load_assets_from_dbt_project(
    DBT_PROJECT_DIR,
    DBT_PROFILES_DIR,
    key_prefix=["ANALYTICS"],
    runtime_metadata_fn=dbt_metadata,
    select="users_cleaned"
)

