
from dagster._utils import file_relative_path
from dagster_dbt import load_assets_from_dbt_project
from dagster import DailyPartitionsDefinition, HourlyPartitionsDefinition

DBT_PROJECT_DIR = file_relative_path(__file__, "../../dbt_project")
DBT_PROFILES_DIR = file_relative_path(__file__, "../../dbt_project/config")

# dbt assets contain some default metadata
# for example dagster will show the schema definitions from
# the dbt project on the asset definition page 
# this function adds extra metadata to each asset materialization
def dbt_metadata(context, node_info):
    return {
        "owner": "data@hooli.com",
        "name": node_info["name"]
    }

# many dbt assets use an incremental approach to avoid
# re-processing all data on each run
# this approach can be modelled in dagster using partitions 
# this project includes assets with hourly and daily partitions
hourly_partitions = HourlyPartitionsDefinition(start_date="2023-05-10-00:00")
daily_partitions = DailyPartitionsDefinition(start_date="2023-05-11")

def partition_key_to_vars(partition_key):
    """ Map dagster partitions to the dbt var used in our model WHERE clauses """
    return {"datetime_to_process": partition_key}

def io_partition_metadata_fn_dt(_):
    """ Tells dagster how to load partitioned dbt assets by mapping a partition to dt column """
    return {"partition_expr": "dt"}

def io_partition_metadata_fn_order_date(_):
    """ Tells dagster how to load partitioned dbt assets by mapping a partition to a column """
    return {"partition_expr": "order_date"}

def io_partition_metadata_fn_users(_):
    """ Tells dagster how to load partitioned dbt assets by mapping a partition to a column """
    return {"partition_expr": "created_at"}

orders_cleaned_hourly = load_assets_from_dbt_project(
    DBT_PROJECT_DIR,
    DBT_PROFILES_DIR,
    key_prefix=["ANALYTICS"],
    runtime_metadata_fn=dbt_metadata,
    partition_key_to_vars_fn=partition_key_to_vars,
    partitions_def=hourly_partitions,
    node_info_to_definition_metadata_fn=io_partition_metadata_fn_dt,
    select="orders_cleaned"
)

orders_augmented_hourly = load_assets_from_dbt_project(
    DBT_PROJECT_DIR,
    DBT_PROFILES_DIR,
    key_prefix=["ANALYTICS"],
    source_key_prefix="ANALYTICS",
    runtime_metadata_fn=dbt_metadata,
    partition_key_to_vars_fn=partition_key_to_vars,
    partitions_def=hourly_partitions,
    node_info_to_definition_metadata_fn=io_partition_metadata_fn_order_date,
    select="orders_augmented"
)

users_cleaned_hourly = load_assets_from_dbt_project(
    DBT_PROJECT_DIR,
    DBT_PROFILES_DIR,
    key_prefix=["ANALYTICS"],
    runtime_metadata_fn=dbt_metadata,
    partition_key_to_vars_fn=partition_key_to_vars,
    partitions_def=hourly_partitions,
    node_info_to_definition_metadata_fn=io_partition_metadata_fn_users,
    select="users_cleaned"
)

daily_dbt_assets = load_assets_from_dbt_project(
    DBT_PROJECT_DIR,
    DBT_PROFILES_DIR,
    key_prefix=["ANALYTICS"],
    source_key_prefix="ANALYTICS",
    runtime_metadata_fn=dbt_metadata,
    partition_key_to_vars_fn=partition_key_to_vars,
    partitions_def=daily_partitions,
    node_info_to_definition_metadata_fn=io_partition_metadata_fn_order_date,
    select="daily_order_summary order_stats",
)

dbt_views = load_assets_from_dbt_project(
    DBT_PROJECT_DIR,
    DBT_PROFILES_DIR,
    key_prefix=["ANALYTICS"],
    source_key_prefix="ANALYTICS",
    runtime_metadata_fn=dbt_metadata,
    select="company_perf sku_stats company_stats"
)



