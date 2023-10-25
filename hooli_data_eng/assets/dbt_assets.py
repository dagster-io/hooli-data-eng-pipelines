from dateutil import parser
import json
from pathlib import Path
import textwrap
from typing import (
    Any,
    Generator,
    Mapping,
    Union,
)

from dagster import (
    AutoMaterializePolicy,
    AutoMaterializeRule,
    AssetKey,
    AssetCheckResult,
    AssetObservation,
    DailyPartitionsDefinition,
    WeeklyPartitionsDefinition,
    OpExecutionContext,
    Output,
    BackfillPolicy,
)
from dagster_dbt.asset_decorator import dbt_assets
from dagster._utils import file_relative_path
from dagster_cloud.dagster_insights import dbt_with_snowflake_insights
from dagster_dbt import (
    DbtCliEventMessage,
    DbtCliInvocation,
    DbtCliResource,
    DagsterDbtTranslator,
    load_assets_from_dbt_project,
    default_metadata_from_dbt_resource_props,
)

# many dbt assets use an incremental approach to avoid
# re-processing all data on each run
# this approach can be modelled in dagster using partitions
# this project includes assets with hourly and daily partitions
daily_partitions = DailyPartitionsDefinition(start_date="2023-05-25")
weekly_partitions = WeeklyPartitionsDefinition(start_date="2023-05-25")

DBT_PROJECT_DIR = file_relative_path(__file__, "../../dbt_project")
DBT_PROFILES_DIR = file_relative_path(__file__, "../../dbt_project/config")


DBT_MANIFEST = Path(
    file_relative_path(__file__, "../../dbt_project/target/manifest.json")
)

allow_outdated_parents_policy = AutoMaterializePolicy.eager().without_rules(
    AutoMaterializeRule.skip_on_parent_outdated()
)

allow_outdated_and_missing_parents_policy = AutoMaterializePolicy.eager().without_rules(
    AutoMaterializeRule.skip_on_parent_outdated(), 
    AutoMaterializeRule.skip_on_parent_missing() # non-partitioned assets should run even if some upstream partitions are missing
)


class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    def get_description(self, dbt_resource_props: Mapping[str, Any]) -> str:
        description = f"dbt model for: {dbt_resource_props['name']} \n \n"

        return description + textwrap.indent(
            dbt_resource_props.get("raw_code", ""), "\t"
        )

    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
        node_path = dbt_resource_props["path"]
        prefix = node_path.split("/")[0]

        if node_path == "models/sources.yml":
            prefix = "RAW_DATA"

        if node_path == "MARKETING/company_perf.sql":
            prefix = "ANALYTICS"

        return AssetKey([prefix, dbt_resource_props["name"]])

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

        if dbt_resource_props["name"] in ["company_perf", "sku_stats", "company_stats"]:
            metadata = {}

        default_metadata = default_metadata_from_dbt_resource_props(dbt_resource_props)

        return {**default_metadata, **metadata}

    def get_auto_materialize_policy(
        self, dbt_resource_props: Mapping[str, Any]
    ):
        return allow_outdated_parents_policy


class CustomDagsterDbtTranslatorForViews(CustomDagsterDbtTranslator):
    def get_auto_materialize_policy(
        self, dbt_resource_props: Mapping[str, Any]
    ):
        return allow_outdated_and_missing_parents_policy

def _process_partitioned_dbt_assets(context: OpExecutionContext, dbt2: DbtCliResource):
    # map partition key range to dbt vars
    first_partition, last_partition = context.asset_partitions_time_window_for_output(
        list(context.selected_output_names)[0]
    )
    dbt_vars = {"min_date": str(first_partition), "max_date": str(last_partition)}
    dbt_args = ["run", "--vars", json.dumps(dbt_vars)]

    dbt_cli_task = dbt2.cli(dbt_args, context=context)

    # This function adds model start and end time to derive total execution time
    def handle_dbt_event(event: DbtCliEventMessage) -> Generator[Union[Output, AssetObservation, AssetCheckResult], None, None]:
        for dagster_event in event.to_default_asset_events(
            manifest=dbt_cli_task.manifest
        ):
            if isinstance(dagster_event, Output):
                event_node_info = event.raw_event["data"]["node_info"]

                started_at = parser.isoparse(event_node_info["node_started_at"])
                completed_at = parser.isoparse(event_node_info["node_finished_at"])
                metadata = {
                    "Execution Started At": started_at.isoformat(timespec="seconds"),
                    "Execution Completed At": completed_at.isoformat(
                        timespec="seconds"
                    ),
                    "Execution Duration": (completed_at - started_at).total_seconds(),
                    "Owner": "data@hooli.com",
                }

                context.add_output_metadata(
                    metadata=metadata,
                    output_name=dagster_event.output_name,
                )
            yield dagster_event
    
    # This function emits an AssetObservation with the dbt model's invocation ID and unique ID (needed for Snowflake Insights)
    def handle_all_dbt_events(dbt_cli_task: DbtCliInvocation) -> Generator[Union[Output, AssetObservation, AssetCheckResult], None, None]:
        for raw_event in dbt_cli_task.stream_raw_events():
            yield from handle_dbt_event(raw_event)

    yield from dbt_with_snowflake_insights(context, dbt_cli_task, dagster_events=handle_all_dbt_events(dbt_cli_task))

    if not dbt_cli_task.is_successful():
        raise Exception("dbt command failed, see preceding events")


@dbt_assets(
    manifest=DBT_MANIFEST,
    select="orders_cleaned users_cleaned orders_augmented",
    partitions_def=daily_partitions,
    dagster_dbt_translator=CustomDagsterDbtTranslator(),
    backfill_policy=BackfillPolicy.single_run(),
)
def daily_dbt_assets(context: OpExecutionContext, dbt2: DbtCliResource):
    yield from _process_partitioned_dbt_assets(context=context, dbt2=dbt2)


@dbt_assets(
    manifest=DBT_MANIFEST,
    select="weekly_order_summary order_stats",
    partitions_def=weekly_partitions,
    dagster_dbt_translator=CustomDagsterDbtTranslator(),
    backfill_policy=BackfillPolicy.single_run(),
)
def weekly_dbt_assets(context: OpExecutionContext, dbt2: DbtCliResource):
    yield from _process_partitioned_dbt_assets(context=context, dbt2=dbt2)


dbt_views = load_assets_from_dbt_project(
    DBT_PROJECT_DIR,
    DBT_PROFILES_DIR,
    #key_prefix=["ANALYTICS"],
    #source_key_prefix="ANALYTICS",
    select="company_perf sku_stats company_stats",
    #node_info_to_group_fn=lambda x: "ANALYTICS",
    dagster_dbt_translator=CustomDagsterDbtTranslatorForViews()
)
