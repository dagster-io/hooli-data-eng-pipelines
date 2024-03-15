
from dagster import (
    Definitions,
    load_assets_from_modules,
    load_assets_from_package_module,
    multiprocess_executor,
)

from hooli_data_eng.assets import forecasting, raw_data, marketing, dbt_assets, amp_test
from hooli_data_eng.assets.dbt_assets import dbt_slim_ci_job
from hooli_data_eng.assets.marketing import check_avg_orders
from hooli_data_eng.assets.raw_data import check_users
from hooli_data_eng.jobs import analytics_job, predict_job
from hooli_data_eng.resources import get_env, resource_def
from hooli_data_eng.schedules import analytics_schedule
from hooli_data_eng.sensors import orders_sensor
from hooli_data_eng.sensors.delayed_asset_alerts import asset_delay_alert_sensor
from hooli_data_eng.sensors.watch_s3 import watch_s3_sensor

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

# Our final set of assets represent Python code that
# should run after dbt. These assets are defined in
# assets/forecasting/__init__.py
forecasting_assets = load_assets_from_package_module(
    forecasting, group_name="FORECASTING"
)

marketing_assets = load_assets_from_package_module(marketing, group_name="MARKETING")

amp_assets = load_assets_from_package_module(amp_test, group_name="AMP_TEST")
# ---------------------------------------------------
# Definitions

# Definitions are the collection of assets, jobs, schedules, resources, and sensors
# used with a project. Dagster Cloud deployments can contain mulitple projects.

defs = Definitions(
    executor=multiprocess_executor.configured(
        {"max_concurrent": 3}
    ),  
    assets=[*dbt_assets, *raw_data_assets, *forecasting_assets, *marketing_assets, *amp_assets],
    asset_checks=[check_users, check_avg_orders],
    resources=resource_def[get_env()],
    schedules=[analytics_schedule],
    sensors=[
       orders_sensor,
       watch_s3_sensor,
       asset_delay_alert_sensor,
    ],
    jobs=[analytics_job, predict_job, dbt_slim_ci_job],
)
