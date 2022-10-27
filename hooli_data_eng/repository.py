import os

from hooli_data_eng.assets import forecasting, raw_data
from dagster_duckdb import build_duckdb_io_manager
from dagster_duckdb_pandas import DuckDBPandasTypeHandler
from dagster_dbt import dbt_cli_resource, load_assets_from_dbt_project
from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake_pandas import SnowflakePandasTypeHandler
from dagster_aws.s3 import s3_resource, s3_pickle_io_manager



from dagster import (
    AssetSelection,
    EventLogEntry,
    RunRequest,
    ScheduleDefinition,
    SensorEvaluationContext,
    ResourceDefinition,
    asset_sensor,
    define_asset_job,
    fs_io_manager,
    load_assets_from_package_module,
    repository,
    with_resources,
    AssetKey
)
from dagster._utils import file_relative_path

# ---------------------------------------------------
# Assets

DBT_PROJECT_DIR = file_relative_path(__file__, "../dbt_project")
DBT_PROFILES_DIR = file_relative_path(__file__, "../dbt_project/config")


dbt_assets = load_assets_from_dbt_project(
    DBT_PROJECT_DIR,
    DBT_PROFILES_DIR,
    key_prefix=["analytics"]
)

raw_data_assets = load_assets_from_package_module(
    raw_data,
    group_name="raw_data",
    key_prefix=["raw_data"]
)

forecasting_assets = load_assets_from_package_module(
    forecasting,
    group_name="forecasting"
)


# ---------------------------------------------------
# Resources

def get_env():
    if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "") == "1":
        return "BRANCH"
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "data-eng-prod":
        return "PROD"
    return "LOCAL"

duckdb_io_manager = build_duckdb_io_manager([DuckDBPandasTypeHandler()]).configured(
    {"duckdb_path": os.path.join(DBT_PROJECT_DIR, "example.duckdb")}
)

snowflake_io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()])

s3 = s3_resource.configured({
            "region_name": "us-west-2"
})


resource_def = {
    "LOCAL": {
        "io_manager": duckdb_io_manager,
        "model_io_manager": fs_io_manager,
        "s3": ResourceDefinition.none_resource(),
        "dbt": dbt_cli_resource.configured({
            "project_dir": DBT_PROJECT_DIR,
            "profiles_dir": DBT_PROFILES_DIR,
            "target": "LOCAL"
        })
    },

    "BRANCH": {
        "io_manager": snowflake_io_manager.configured({
            "database":  "DEMO_DB2_BRANCH",
            "account": {"env": "SNOWFLAKE_ACCOUNT"},
            "user": {"env": "SNOWFLAKE_USER"},
            "password": {"env": "SNOWFLAKE_PASSWORD"},
            "warehouse": "TINY_WAREHOUSE"
        }),
        "model_io_manager": s3_pickle_io_manager.configured({
            "s3_bucket": "hooli-demo-branch"
        }),
        "s3": s3,
        "dbt": dbt_cli_resource.configured({
            "project_dir": DBT_PROJECT_DIR,
            "profiles_dir": DBT_PROFILES_DIR,
            "target": "BRANCH"
        })

    },

    "PROD": {
        "io_manager": snowflake_io_manager.configured({
            "database":  "DEMO_DB2",
            "account": {"env": "SNOWFLAKE_ACCOUNT"},
            "user": {"env": "SNOWFLAKE_USER"},
            "password": {"env": "SNOWFLAKE_PASSWORD"},
            "warehouse": "TINY_WAREHOUSE"
        }),
        "model_io_manager": s3_pickle_io_manager.configured({
            "s3_bucket": "hooli-demo"
        }),
        "s3": s3,
        "dbt": dbt_cli_resource.configured({
            "project_dir": DBT_PROJECT_DIR,
            "profiles_dir": DBT_PROFILES_DIR,
            "target": "PROD"
        })

    }
}

assets_with_resources = with_resources(
        dbt_assets + raw_data_assets + forecasting_assets,
        resource_def[get_env()]
) 

# ---------------------------------------------------
# Jobs and Sensors

analytics_job = define_asset_job("refresh_analytics_model_job",
     selection=AssetSelection.keys(["analytics", "daily_order_summary"]).upstream(), 
    #  config = {
    #     "resources": resource_def[get_env()]
    #  }
)

predict_job = define_asset_job("predict_job", 
    selection=AssetSelection.keys(["forecasting","predicted_orders"]),
    # config = {
    #     "resources": resource_def[get_env()]
    #  }
)

@asset_sensor(asset_key=AssetKey(["analytics", "orders_augmented"]), job = predict_job)
def orders_sensor(context: SensorEvaluationContext, asset_event: EventLogEntry):
    yield RunRequest(
        run_key = context.cursor
    )


# ---------------------------------------------------
# Repository

@repository
def hooli_data_eng():
    return assets_with_resources + [
        ScheduleDefinition(job=analytics_job, cron_schedule="0 * * * *")
    ] + [ 
    orders_sensor 
    ] + [
        analytics_job, predict_job
    ]