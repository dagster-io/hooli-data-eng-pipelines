import os

from dagster_pyspark import pyspark_resource

from hooli_data_eng.assets import forecasting, raw_data, marketing
from hooli_data_eng.resources.databricks import db_step_launcher
from hooli_data_eng.resources.api import data_api
from hooli_data_eng.jobs.watch_s3 import watch_s3_sensor
from dagster_duckdb import build_duckdb_io_manager
from dagster_duckdb_pandas import DuckDBPandasTypeHandler
from dagster_dbt import dbt_cli_resource, load_assets_from_dbt_project
from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake_pandas import SnowflakePandasTypeHandler
from dagster_aws.s3 import s3_resource, s3_pickle_io_manager
from dagster_databricks import databricks_pyspark_step_launcher
from dagstermill import local_output_notebook_io_manager

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
    AssetKey,
    build_asset_reconciliation_sensor
)
from dagster._utils import file_relative_path

# ---------------------------------------------------
# Assets

# Dagster assets specify what outputs we care about and 
# the logical code needed to create them

# Our first set of assets represent raw data, and the asset
# definitions can be seen in /assets/raw_data/__init__.py
# 
# These raw datasets will be used by dbt as dbt sources
# which can be found in dbt_project/models/sources.yml
raw_data_assets = load_assets_from_package_module(
    raw_data,
    group_name="RAW_DATA",
    key_prefix=['RAW_DATA']
)

# Our second set of assets represent dbt models
# these models are defined in the dbt_project
# folder
# 
# The dbt file dbt_project/config/profiles.yaml 
# specifies what databases to targets, and locally will 
# execute against a DuckDB
DBT_PROJECT_DIR = file_relative_path(__file__, "../dbt_project")
DBT_PROFILES_DIR = file_relative_path(__file__, "../dbt_project/config")

dbt_assets = load_assets_from_dbt_project(
    DBT_PROJECT_DIR,
    DBT_PROFILES_DIR,
    key_prefix=["ANALYTICS"]
)


# Our final set of assets represent Python code that
# should run after dbt. These assets are defined in 
# assets/forecasting/__init__.py
forecasting_assets = load_assets_from_package_module(
    forecasting,
    group_name="FORECASTING"
)

marketing_assets = load_assets_from_package_module(
    marketing,
    group_name="MARKETING"
)

# ---------------------------------------------------
# Resources

# Resources represent external systems and, and specifically IO Managers
# tell dagster where our assets should be materialized. In dagster 
# resources are separate from logical code to make it possible
# to develop locally, run tests, and run integration tests
# 
# This project is designed for everything to run locally 
# using the file system and DuckDB as the primary development resources
#
# PRs use a "branch" environment that mirrors production with 
# staging Snowflake and S3 resources
#
# The production deployment on Dagster Cloud uses production Snowflake
# and S3 resources

def get_env():
    if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "") == "1":
        return "BRANCH"
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "data-eng-prod":
        return "PROD"
    return "LOCAL"

# Locally, have dagster use DuckDB as the database
# See dbt_project/config/profiles.yml to see the matching dbt config
duckdb_io_manager = build_duckdb_io_manager([DuckDBPandasTypeHandler()]).configured(
    {"database": os.path.join(DBT_PROJECT_DIR, "example.duckdb")}
)

# For production we'll use snowflake and s3
snowflake_io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()])
s3 = s3_resource.configured({ "region_name": "us-west-2"})

# Similar to having different dbt targets, here we create the resource
# configuration by environment
resource_def = {
    "LOCAL": {
        "io_manager": duckdb_io_manager,
        "model_io_manager": fs_io_manager,
        "output_notebook_io_manager": local_output_notebook_io_manager,
        "data_api": data_api,
        "s3": ResourceDefinition.none_resource(),
        "dbt": dbt_cli_resource.configured({
            "project_dir": DBT_PROJECT_DIR,
            "profiles_dir": DBT_PROFILES_DIR,
            "target": "LOCAL"
        }),
        "pyspark": pyspark_resource,
        "step_launcher": ResourceDefinition.none_resource()
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
        "output_notebook_io_manager": local_output_notebook_io_manager,
        "data_api": data_api,
        "s3": s3,
        "dbt": dbt_cli_resource.configured({
            "project_dir": DBT_PROJECT_DIR,
            "profiles_dir": DBT_PROFILES_DIR,
            "target": "BRANCH"
        }),
        "pyspark": pyspark_resource,
        "step_launcher": db_step_launcher

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
        "output_notebook_io_manager": local_output_notebook_io_manager,
        "s3": s3,
        "data_api": data_api,
        "dbt": dbt_cli_resource.configured({
            "project_dir": DBT_PROJECT_DIR,
            "profiles_dir": DBT_PROFILES_DIR,
            "target": "PROD"
        }),
        "pyspark": pyspark_resource,
        "step_launcher": db_step_launcher

    }
}

assets_with_resources = with_resources(
        dbt_assets + raw_data_assets + forecasting_assets + marketing_assets,
        resource_def[get_env()]
) 

# ---------------------------------------------------
# Jobs and Sensors

# With assets defined we have everything to run Dagster
# ourselves if we wanted to manually create assets. 
# Most of the time you will want to automate asset creation.
# In dagster, jobs allow you to update all or some assets.
# Jobs can be run on a schedule, or in response to an external 
# event using a sensor.

# This job updates all of the assets upstream of "daily_order_summary",
# which is an asset representing a model in dbt. In this case, 
# this job will update the raw data assets and then the dbt models
# upstream of daily_order_summary.
analytics_job = define_asset_job("refresh_analytics_model_job",
     selection=AssetSelection.keys(["ANALYTICS", "daily_order_summary"]).upstream(), 
)

# This schedule tells dagster to run the analytics_job daily
analytics_schedule = ScheduleDefinition(job=analytics_job, cron_schedule="0 * * * *")

# This job selects the predicted_orders asset defined in 
# assets/forecasting/__init__.py
predict_job = define_asset_job("predict_job", 
    selection=AssetSelection.keys(["FORECASTING","predicted_orders"]),
)


# This sensor listens for changes to the orders_augmented asset which 
# represents a dbt model. When the table managed by dbt is updated, 
# this sensor will trigger the predict_job above, ensuring that anytime 
# new order data is produced the forecast is updated
@asset_sensor(asset_key=AssetKey(["ANALYTICS", "orders_augmented"]), job = predict_job)
def orders_sensor(context: SensorEvaluationContext, asset_event: EventLogEntry):
    yield RunRequest(
        run_key = context.cursor
    )

freshness_sla_sensor = build_asset_reconciliation_sensor(
    name = "freshness_sla_sensor",
    asset_selection = AssetSelection.keys(AssetKey(["MARKETING", "avg_order"])).upstream()
)

# ---------------------------------------------------
# Repository

# A repository is the collection of assets, jobs, schedules, and sensors.
# Dagster Cloud deployments can contain mulitple repositories.

@repository
def hooli_data_eng():
    return assets_with_resources + [analytics_schedule] + [orders_sensor, watch_s3_sensor, freshness_sla_sensor] + [analytics_job, predict_job]