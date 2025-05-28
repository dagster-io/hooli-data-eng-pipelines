from datetime import datetime
import dagster as dg
from dagster_dbt import DbtCliResource, DagsterDbtTranslatorSettings
from hooli_data_eng.defs.dbt.resources import dbt_project
from hooli_data_eng.defs.dbt.assets import weekly_freshness_check
from hooli_data_eng.defs.dbt.dbt_code_version import get_current_dbt_code_version
from hooli_data_eng.defs.dbt.assets import (
    regular_dbt_assets,
    CustomDagsterDbtTranslator,
)

DBT_MANIFEST = dbt_project.manifest_path

weekly_freshness_check_sensor = dg.build_sensor_for_freshness_checks(
    freshness_checks=weekly_freshness_check, name="weekly_freshness_check_sensor"
)

# This job updates all of the assets upstream of "orders_augmented",
# which is an asset representing a model in dbt
analytics_job = dg.define_asset_job(
    name="refresh_analytics_model_job",
    selection=dg.AssetSelection.keys(["ANALYTICS", "orders_augmented"]).upstream()
    - dg.AssetSelection.keys(["CLEANED", "locations_cleaned"]),
    tags={"dagster/max_retries": "1"},
    # config = {"execution": {"config": {"multiprocess": {"max_concurrent": 1}}}}
)

# This schedule tells dagster to run the analytics_job daily
analytics_schedule = dg.build_schedule_from_partitioned_job(analytics_job)


# This op will be used to run slim CI
@dg.op(out={})
def dbt_slim_ci(dbt: DbtCliResource):
    dbt_command = [
        "build",
        "--select",
        "state:modified.body+",
        "--defer",
        "--state",
        dbt.state_path,
    ]

    yield from (
        dbt.cli(
            args=dbt_command,
            manifest=DBT_MANIFEST,
            dagster_dbt_translator=CustomDagsterDbtTranslator(
                DagsterDbtTranslatorSettings(
                    enable_asset_checks=True,
                    enable_code_references=True,
                )
            ),
        )
        .stream()
        .fetch_row_counts()
        .fetch_column_metadata()
    )


# This job will be triggered by Pull Request and should only run new or changed dbt models
@dg.job
def dbt_slim_ci_job():
    dbt_slim_ci()


@dg.sensor(asset_selection=dg.AssetSelection.assets(regular_dbt_assets))
def dbt_code_version_sensor(context: dg.SensorEvaluationContext):
    context.log.info(f"Checking code versions for assets: {regular_dbt_assets.keys}")
    assets_to_materialize = []
    for asset_key in regular_dbt_assets.keys:
        latest_materialization = context.instance.get_latest_materialization_event(
            asset_key
        )
        if latest_materialization:
            latest_code_version = latest_materialization.asset_materialization.tags.get(
                "dagster/code_version"
            )
            context.log.info(
                f"Latest code version for {asset_key}: {latest_code_version}"
            )
            current_code_version = get_current_dbt_code_version(
                asset_key
            )  # Implement this function to get the current code version
            context.log.info(
                f"Current code version for {asset_key}: {current_code_version}"
            )
            if latest_code_version != current_code_version:
                assets_to_materialize.append(asset_key)
    context.log.info(f"Assets to materialize: {assets_to_materialize}")
    if assets_to_materialize:
        yield dg.RunRequest(
            run_key=f"code_version_update_{datetime.now()}",
            asset_selection=list(assets_to_materialize),
        )
