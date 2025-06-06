import json
import textwrap
from typing import Any, Mapping
import dagster as dg
from dagster_dbt import (
    DbtCliResource,
    DagsterDbtTranslator,
    default_metadata_from_dbt_resource_props,
    DagsterDbtTranslatorSettings,
)
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.freshness_builder import build_freshness_checks_from_dbt_assets
from dagster_cloud.dagster_insights import dbt_with_snowflake_insights
from hooli_data_eng.defs.dbt.resources import dbt_project

# many dbt assets use an incremental approach to avoid
# re-processing all data on each run
# this approach can be modelled in dagster using partitions
# this project includes assets with hourly and daily partitions
daily_partitions = dg.DailyPartitionsDefinition(start_date="2023-05-25")
weekly_partitions = dg.WeeklyPartitionsDefinition(start_date="2023-05-25")


DBT_MANIFEST = dbt_project.manifest_path


allow_outdated_parents_policy = (
    dg.AutomationCondition.eager().as_auto_materialize_policy()
)


became_missing_or_any_parents_updated = (
    dg.AutomationCondition.missing().newly_true().with_label("became missing")
    | dg.AutomationCondition.any_deps_match(
        dg.AutomationCondition.newly_updated()
        | dg.AutomationCondition.will_be_requested()
    ).with_label("any parents updated")
)

allow_outdated_and_missing_parents_condition = (
    dg.AutomationCondition.in_latest_time_window()
    & became_missing_or_any_parents_updated.since(
        dg.AutomationCondition.newly_requested()
        | dg.AutomationCondition.newly_updated()
    )
    & ~dg.AutomationCondition.in_progress()
).with_label(
    "update non-partitioned asset while allowing some missing or outdated parent partitions"
)


class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    def get_description(self, dbt_resource_props: Mapping[str, Any]) -> str:
        description = f"dbt model for: {dbt_resource_props['name']} \n \n"

        return description + textwrap.indent(
            dbt_resource_props.get("raw_code", ""), "\t"
        )

    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> dg.AssetKey:
        node_path = dbt_resource_props["path"]
        prefix = node_path.split("/")[0]

        if node_path == "models/sources.yml":
            prefix = "RAW_DATA"

        if node_path == "MARKETING/company_perf.sql":
            prefix = "ANALYTICS"

        return dg.AssetKey([prefix, dbt_resource_props["name"]])

    def get_group_name(self, dbt_resource_props: Mapping[str, Any]):
        node_path = dbt_resource_props["path"]
        prefix = node_path.split("/")[0]

        if node_path == "models/sources.yml":
            prefix = "RAW_DATA"

        if node_path == "MARKETING/company_perf.sql":
            prefix = "ANALYTICS"
        return prefix

    def get_metadata(self, dbt_resource_props: Mapping[str, Any]) -> Mapping[str, Any]:
        metadata = {"partition_expr": "order_date"}

        if dbt_resource_props["name"] == "orders_cleaned":
            metadata = {"partition_expr": "dt"}

        if dbt_resource_props["name"] == "users_cleaned":
            metadata = {"partition_expr": "created_at"}

        default_metadata = default_metadata_from_dbt_resource_props(dbt_resource_props)

        return {**default_metadata, **metadata}

    def get_automation_condition(self, dbt_resource_props: Mapping[str, Any]):
        if dbt_resource_props["name"] in [
            "company_stats",
            "locations_cleaned",
            "weekly_order_summary",
            "order_stats",
        ]:
            return allow_outdated_and_missing_parents_condition

        if dbt_resource_props["name"] in ["sku_stats"]:
            return dg.AutomationCondition.on_cron("0 0 1 * *")

        if dbt_resource_props["name"] in ["company_perf"]:
            return dg.AutomationCondition.any_downstream_conditions()

    def get_owners(self, dbt_resource_props: Mapping[str, Any]):
        return (
            [
                dbt_resource_props.get["groups"]["owner"]["email"],
                f"team:{dbt_resource_props['groups']['name']}",
            ]
            if dbt_resource_props.get("groups") is not None
            else []
        )


def _process_partitioned_dbt_assets(
    context: dg.AssetExecutionContext, dbt: DbtCliResource
):
    # map partition key range to dbt vars
    first_partition, last_partition = context.partition_time_window
    dbt_vars = {"min_date": str(first_partition), "max_date": str(last_partition)}
    dbt_args = ["build", "--vars", json.dumps(dbt_vars)]

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


@dbt_assets(
    manifest=DBT_MANIFEST,
    project=dbt_project,
    select="orders_cleaned users_cleaned orders_augmented",
    partitions_def=daily_partitions,
    dagster_dbt_translator=CustomDagsterDbtTranslator(
        settings=DagsterDbtTranslatorSettings(
            enable_asset_checks=True,
            enable_code_references=True,
        )
    ),
    backfill_policy=dg.BackfillPolicy.single_run(),
)
def daily_dbt_assets(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from _process_partitioned_dbt_assets(context=context, dbt=dbt)


@dbt_assets(
    manifest=DBT_MANIFEST,
    project=dbt_project,
    select="weekly_order_summary order_stats",
    partitions_def=weekly_partitions,
    dagster_dbt_translator=CustomDagsterDbtTranslator(
        DagsterDbtTranslatorSettings(
            enable_asset_checks=True,
            enable_code_references=True,
        )
    ),
    backfill_policy=dg.BackfillPolicy.single_run(),
)
def weekly_dbt_assets(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from _process_partitioned_dbt_assets(context=context, dbt=dbt)


weekly_freshness_check = build_freshness_checks_from_dbt_assets(
    dbt_assets=[weekly_dbt_assets]
)


@dbt_assets(
    manifest=DBT_MANIFEST,
    project=dbt_project,
    select="company_stats locations_cleaned sku_stats company_perf",
    dagster_dbt_translator=CustomDagsterDbtTranslator(
        DagsterDbtTranslatorSettings(
            enable_asset_checks=True,
            enable_code_references=True,
        )
    ),
)
def regular_dbt_assets(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    # Invoke dbt CLI
    dbt_cli_task = dbt.cli(["build"], context=context)

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
