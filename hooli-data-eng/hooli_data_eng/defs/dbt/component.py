import json
from typing import Union, Literal, Optional
import dagster as dg
from hooli_data_eng.utils import get_env
from dagster_dbt import (
    DbtCliResource,
)
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.freshness_builder import build_freshness_checks_from_dbt_assets
from dagster_cloud.dagster_insights import dbt_with_snowflake_insights
from hooli_data_eng.defs.dbt.resources import dbt_project
from datetime import datetime
from hooli_data_eng.defs.dbt.dbt_code_version import get_current_dbt_code_version
from hooli_data_eng.defs.dbt.resources import resource_def
from hooli_data_eng.defs.dbt.slim_ci import get_slim_ci_job
from hooli_data_eng.defs.dbt.translator import get_hooli_translator

from datetime import timedelta
from dagster.preview.freshness import apply_freshness_policy
from dagster.preview.freshness import FreshnessPolicy

# many dbt assets use an incremental approach to avoid
# re-processing all data on each run
# this approach can be modelled in dagster using partitions
# this project includes assets with hourly and daily partitions
daily_partitions = dg.DailyPartitionsDefinition(start_date="2023-05-25")
weekly_partitions = dg.WeeklyPartitionsDefinition(start_date="2023-05-25")


def _process_partitioned_dbt_assets(
    context: dg.AssetExecutionContext, dbt: DbtCliResource
):
    # Check if the asset is partitioned
    if context.has_partition_key:
        # map partition key range to dbt vars
        first_partition, last_partition = context.partition_time_window
        dbt_vars = {"min_date": str(first_partition), "max_date": str(last_partition)}
        dbt_args = ["build", "--vars", json.dumps(dbt_vars)]
    else:
        # if not partitioned, use default dbt build command
        dbt_args = ["build"]

    # Invoke dbt CLI
    dbt_cli_task = dbt.cli(dbt_args, context=context)

    # Emits an AssetObservation for each asset materialization, which is used to
    # identify the Snowflake credit consumption
    yield from dbt_with_snowflake_insights(
        context=context,
        dbt_cli_invocation=dbt_cli_task,
        dagster_events=dbt_cli_task.stream().fetch_row_counts().fetch_column_metadata(),
    )

    # fetch run_results.json to log compiled SQL
    run_results_json = dbt_cli_task.get_artifact("run_results.json")
    for result in run_results_json["results"]:
        model_name = result.get("unique_id")
        context.log.info(f"Compiled SQL for {model_name}:\n{result['compiled_code']}")


class DbtSelection(dg.Resolvable, dg.Model):
    selection: str
    partitioning: Optional[Union[Literal["weekly"], Literal["daily"]]] = None
    freshness_check_sensor: Optional[str] = None
    run_on_code_version_change: bool = False


class HooliDbtComponent(dg.Component, dg.Resolvable, dg.Model):
    groups: list[DbtSelection]

    def build_defs(self, context) -> dg.Definitions:
        assets = []
        checks = []
        sensors = []

        weekly_policy = FreshnessPolicy.time_window(
            fail_window=timedelta(days=7),
            warn_window=timedelta(days=2),
        )

        daily_policy = FreshnessPolicy.time_window(
            fail_window=timedelta(hours=24),
            warn_window=timedelta(hours=12),
        )

        regular_policy = FreshnessPolicy.time_window(
            fail_window=timedelta(days=7),
            warn_window=timedelta(days=3),
        )

        for group in self.groups:
            backfill_policy = None
            partitions_def = None
            name = "regular"
            if group.partitioning == "weekly":
                name = group.partitioning
                backfill_policy = dg.BackfillPolicy.single_run()
                partitions_def = weekly_partitions

            if group.partitioning == "daily":
                name = group.partitioning
                backfill_policy = dg.BackfillPolicy.single_run()
                partitions_def = daily_partitions

            @dbt_assets(
                name=f"{name}_dbt_assets",
                manifest=dbt_project.manifest_path,
                project=dbt_project,
                select=group.selection,
                partitions_def=partitions_def,
                dagster_dbt_translator=get_hooli_translator(),
                backfill_policy=backfill_policy,
            )
            def _dbt_asset(context: dg.AssetExecutionContext, dbt: DbtCliResource):
                yield from _process_partitioned_dbt_assets(context=context, dbt=dbt)

            assets.append(_dbt_asset)

            checks.extend(dg.build_column_schema_change_checks(assets=[_dbt_asset]))

            if group.freshness_check_sensor:
                freshness_checks = build_freshness_checks_from_dbt_assets(
                    dbt_assets=[_dbt_asset]
                )
                checks.extend(freshness_checks)
                sensors.append(
                    dg.build_sensor_for_freshness_checks(
                        freshness_checks=freshness_checks,
                        name=group.freshness_check_sensor,
                    )
                )

            if group.run_on_code_version_change:
                sensors.append(build_code_version_sensor(_dbt_asset))

        defs = dg.Definitions(
            assets=assets,
            asset_checks=checks,
            sensors=sensors,
            resources=resource_def[get_env()],
            jobs=[get_slim_ci_job()],
        )

        defs = defs.map_resolved_asset_specs(
            func=lambda spec: apply_freshness_policy(spec, daily_policy),
            selection='key:"ANALYTICS/orders_augmented"or key:"CLEANED/orders_cleaned"or key:"CLEANED/users_cleaned"',
        )
        defs = defs.map_resolved_asset_specs(
            func=lambda spec: apply_freshness_policy(spec, weekly_policy),
            selection='key:"ANALYTICS/order_stats" or key:"ANALYTICS/weekly_order_summary"',
        )
        defs = defs.map_resolved_asset_specs(
            func=lambda spec: apply_freshness_policy(spec, regular_policy),
            selection='key:"CLEANED/locations_cleaned" or key:"ANALYTICS/company_stats" or key:"ANALYTICS/company_perf" or key:"ANALYTICS/sku_stats"',
        )

        return defs


def build_code_version_sensor(target_assets: dg.AssetsDefinition):
    @dg.sensor(asset_selection=dg.AssetSelection.assets(target_assets))
    def dbt_code_version_sensor(context: dg.SensorEvaluationContext):
        context.log.info(f"Checking code versions for assets: {target_assets.keys}")
        assets_to_materialize = []
        for asset_key in target_assets.keys:
            latest_materialization = context.instance.get_latest_materialization_event(
                asset_key
            )
            if latest_materialization:
                latest_code_version = (
                    latest_materialization.asset_materialization.tags.get(
                        "dagster/code_version"
                    )
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

    return dbt_code_version_sensor
