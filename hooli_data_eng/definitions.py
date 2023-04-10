import os

from dagster_pyspark import pyspark_resource

from hooli_data_eng.assets import forecasting, raw_data, marketing, dbt_assets
from hooli_data_eng.assets.delayed_asset_alerts import asset_delay_alert_sensor
from hooli_data_eng.resources.sensor_file_managers import s3FileSystem, LocalFileSystem
from hooli_data_eng.resources.sensor_smtp import LocalEmailAlert, SESEmailAlert
from hooli_data_eng.resources.databricks import db_step_launcher
from hooli_data_eng.resources.api import RawDataAPI
from hooli_data_eng.jobs.watch_s3 import watch_s3_sensor
from dagster_duckdb_pandas import DuckDBPandasIOManager
from dagster_dbt import dbt_cli_resource
from dagster_snowflake_pandas import SnowflakePandasIOManager
from dagster_aws.s3 import s3_pickle_io_manager, s3_resource
from dagstermill import local_output_notebook_io_manager

from dagster import (
    build_schedule_from_partitioned_job,
    AssetSelection,
    Definitions,
    EnvVar,
    EventLogEntry,
    RunRequest,
    ScheduleDefinition,
    SensorEvaluationContext,
    ResourceDefinition,
    asset_sensor,
    define_asset_job,
    fs_io_manager,
    load_assets_from_modules,
    load_assets_from_package_module,
    AssetKey,
    build_asset_reconciliation_sensor,
    multiprocess_executor,
    ConfigurableResource,
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
    raw_data, group_name="RAW_DATA", key_prefix=["RAW_DATA"]
)

# Our second set of assets represent dbt models
# these models are defined in the dbt_project
# folder
#
# The dbt file dbt_project/config/profiles.yaml
# specifies what databases to targets, and locally will
# execute against a DuckDB
dbt_assets = load_assets_from_modules([dbt_assets])

DBT_PROJECT_DIR = file_relative_path(__file__, "../dbt_project")
DBT_PROFILES_DIR = file_relative_path(__file__, "../dbt_project/config")

# Our final set of assets represent Python code that
# should run after dbt. These assets are defined in
# assets/forecasting/__init__.py
forecasting_assets = load_assets_from_package_module(
    forecasting, group_name="FORECASTING"
)

marketing_assets = load_assets_from_package_module(marketing, group_name="MARKETING")

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

# Similar to having different dbt targets, here we create the resource
# configuration by environment
s3 = s3_resource.configured({ "region_name": "us-west-2"})

resource_def = {
    "LOCAL": {
        "io_manager": DuckDBPandasIOManager(database=os.path.join(DBT_PROJECT_DIR, "example.duckdb")),
        "model_io_manager": fs_io_manager,
        "output_notebook_io_manager": local_output_notebook_io_manager,
        "data_api": RawDataAPI(),
        "s3": ResourceDefinition.none_resource(),
        "dbt": dbt_cli_resource.configured(
            {
                "project_dir": DBT_PROJECT_DIR,
                "profiles_dir": DBT_PROFILES_DIR,
                "target": "LOCAL",
            }
        ),
        "pyspark": pyspark_resource,
        "step_launcher": ResourceDefinition.none_resource(),
        "monitor_fs": LocalFileSystem(base_dir=file_relative_path(__file__, ".")),
        "email": LocalEmailAlert(smtp_email_to=["data@awesome.com"], smtp_email_from="no-reply@awesome.com"),
    },
    "BRANCH": {
        "io_manager": SnowflakePandasIOManager(
            database="DEMO_DB2_BRANCH", 
            account=EnvVar("SNOWFLAKE_ACCOUNT"),
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
            warehouse="TINY_WAREHOUSE"
        ),
        "s3": s3,
        "model_io_manager": s3_pickle_io_manager.configured({
            "s3_bucket": "hooli-demo-branch"
        }),
        "output_notebook_io_manager": local_output_notebook_io_manager,
        "data_api": RawDataAPI(),
        "dbt": dbt_cli_resource.configured(
            {
                "project_dir": DBT_PROJECT_DIR,
                "profiles_dir": DBT_PROFILES_DIR,
                "target": "BRANCH",
            }
        ),
        "pyspark": pyspark_resource,
        "step_launcher": db_step_launcher,
        "monitor_fs": s3FileSystem(
            region_name="us-west-2", s3_bucket="hooli-demo-branch"
        ),
        "email": ResourceDefinition.none_resource(),
    },
    "PROD": {
        "io_manager": SnowflakePandasIOManager(
            database="DEMO_DB2", 
            account=EnvVar("SNOWFLAKE_ACCOUNT"),
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
            warehouse="TINY_WAREHOUSE"
        ),
        "s3": s3,
        "model_io_manager": s3_pickle_io_manager.configured({
            "s3_bucket": "hooli-demo"
        }),
        "output_notebook_io_manager": local_output_notebook_io_manager,
        "data_api": RawDataAPI(),
        "dbt": dbt_cli_resource.configured(
            {
                "project_dir": DBT_PROJECT_DIR,
                "profiles_dir": DBT_PROFILES_DIR,
                "target": "PROD",
            }
        ),
        "pyspark": pyspark_resource,
        "step_launcher": db_step_launcher,
        "monitor_fs": s3FileSystem(region_name="us-west-2", s3_bucket="hooli-demo"),
        "email": SESEmailAlert(
            smtp_host="email-smtp.us-west-2.amazonaws.com", 
            smtp_email_from="lopp@elementl.com", 
            smtp_email_to= ["lopp@elementl.com"], 
            smtp_username=EnvVar("SMTP_USERNAME"), 
            smtp_password=EnvVar("SMTP_PASSWORD")
        )
    },
}

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
analytics_job = define_asset_job(
     name = "refresh_analytics_model_job",
     selection=AssetSelection.keys(["ANALYTICS", "orders_augmented"]).upstream(), 
     tags = {"dagster/max_retries": "1"},
     # config = {"execution": {"config": {"multiprocess": {"max_concurrent": 1}}}}
)

# This schedule tells dagster to run the analytics_job daily
analytics_schedule = build_schedule_from_partitioned_job(analytics_job)

# This job selects the predicted_orders asset defined in
# assets/forecasting/__init__.py
predict_job = define_asset_job(
    "predict_job",
    selection=AssetSelection.keys(["FORECASTING", "predicted_orders"]),
    tags={"alert_team": "ml"},
)


# This sensor listens for changes to the orders_augmented asset which
# represents a dbt model. When the table managed by dbt is updated,
# this sensor will trigger the predict_job above, ensuring that anytime
# new order data is produced the forecast is updated
@asset_sensor(asset_key=AssetKey(["ANALYTICS", "orders_augmented"]), job=predict_job)
def orders_sensor(context: SensorEvaluationContext, asset_event: EventLogEntry):
    yield RunRequest(run_key=context.cursor)


# This sensor kicks off runs when assets are stale and violoating their
# freshness policies
freshness_sla_sensor = build_asset_reconciliation_sensor(
    name="freshness_sla_sensor",
    minimum_interval_seconds=9,
    asset_selection=AssetSelection.keys(AssetKey(["MARKETING", "avg_order"])).upstream()
    | AssetSelection.keys(AssetKey(["ANALYTICS", "daily_order_summary"])).upstream(),
    run_tags={"dagster/max_retries": "2"},
)

# ---------------------------------------------------
# Definitions

# Definitions are the collection of assets, jobs, schedules, resources, and sensors
# used with a project. Dagster Cloud deployments can contain mulitple projects.

defs = Definitions(
    executor=multiprocess_executor.configured(
        {"max_concurrent": 3}
    ),  # should executors be config driven instead of .configured?
    assets=[*dbt_assets, *raw_data_assets, *forecasting_assets, *marketing_assets],
    resources=resource_def[get_env()],
    schedules=[analytics_schedule],
    sensors=[
        orders_sensor,
        watch_s3_sensor,
        freshness_sla_sensor,
        asset_delay_alert_sensor,
    ],
    jobs=[analytics_job, predict_job],
)
