import hashlib
import json
from dagster import (
    asset_sensor,
    sensor,
    AssetKey,
    EventLogEntry,
    RunRequest,
    SensorEvaluationContext,
    AssetSelection,
    SensorDefinition,
    DagsterInstance,
)
from datetime import datetime
from hooli_data_eng.jobs import predict_job


from hooli_data_eng.assets.dbt_assets import views_dbt_assets
from hooli_data_eng.project import dbt_project

# This sensor listens for changes to the orders_augmented asset which
# represents a dbt model. When the table managed by dbt is updated,
# this sensor will trigger the predict_job above, ensuring that anytime
# new order data is produced the forecast is updated
@asset_sensor(asset_key=AssetKey(["ANALYTICS", "orders_augmented"]), job=predict_job)
def orders_sensor(context: SensorEvaluationContext, asset_event: EventLogEntry):
    yield RunRequest(run_key=context.cursor)


def get_current_dbt_code_version(asset_key: AssetKey) -> str:
    with open(dbt_project.manifest_path) as f:
        manifest = json.load(f)
    
    model_name = asset_key.path[-1]
    model_sql = manifest["nodes"][f"model.dbt_project.{model_name}"]["raw_code"]
    
    return hashlib.sha1(model_sql.encode("utf-8")).hexdigest()


@sensor(asset_selection=AssetSelection.assets(views_dbt_assets))
def my_dbt_code_version_sensor(context: SensorEvaluationContext):
    #asset_keys = [AssetKey("my_dbt_model_1"), AssetKey("my_dbt_model_2")]  # List your dbt asset keys here
    
    context.log.info(f"Checking code versions for assets: {views_dbt_assets.keys}")
    print(f"Checking code versions for assets: {views_dbt_assets.keys}")
    assets_to_materialize = []
    for asset_key in views_dbt_assets.keys:
        # instance = DagsterInstance.get()
        latest_materialization = context.instance.get_latest_materialization_event(asset_key)
        if latest_materialization:
            latest_code_version = latest_materialization.asset_materialization.tags.get("dagster/code_version")
            context.log.info(f"Latest code version for {asset_key}: {latest_code_version}")
            current_code_version = get_current_dbt_code_version(asset_key)  # Implement this function to get the current code version
            context.log.info(f"Current code version for {asset_key}: {current_code_version}")
            if latest_code_version != current_code_version:
                assets_to_materialize.append(asset_key)
    context.log.info(f"Assets to materialize: {assets_to_materialize}")
    if assets_to_materialize:
        yield RunRequest(
            run_key=f"code_version_update_{datetime.now()}",
            asset_selection=list(assets_to_materialize)
            )
    # if never materialized before, materialize all
    # currently doesn't work
    # else:
    #     yield RunRequest(
    #         run_key=f"code_version_update_{datetime.now()}",
    #         asset_selection=list(views_dbt_assets.keys) 
    #     )