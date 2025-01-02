import json
import textwrap
from typing import Any, Mapping

from dagster import (
    AutomationCondition,
    AssetKey,
    BackfillPolicy,
    DailyPartitionsDefinition,
    job,
    op,
    AssetExecutionContext,
    WeeklyPartitionsDefinition,
    AssetCheckExecutionContext,
    AssetCheckResult,
    AssetCheckSpec,
    multi_asset_check,
    AssetCheckSeverity,
)
from dagster_cloud.dagster_insights import dbt_with_snowflake_insights
from dagster_dbt import (
    DbtCliResource,
    DagsterDbtTranslator,
    default_metadata_from_dbt_resource_props,
    DagsterDbtTranslatorSettings,
)

from dagster_dbt.asset_decorator import dbt_assets
from hooli_data_eng.resources import dbt_project
from dagster_dbt.freshness_builder import build_freshness_checks_from_dbt_assets
from dagster import build_sensor_for_freshness_checks

# many dbt assets use an incremental approach to avoid
# re-processing all data on each run
# this approach can be modelled in dagster using partitions
# this project includes assets with hourly and daily partitions
daily_partitions = DailyPartitionsDefinition(start_date="2023-05-25")
weekly_partitions = WeeklyPartitionsDefinition(start_date="2023-05-25")


DBT_MANIFEST = dbt_project.manifest_path


allow_outdated_parents_policy = AutomationCondition.eager().as_auto_materialize_policy()


became_missing_or_any_parents_updated = (
    AutomationCondition.missing().newly_true().with_label("became missing")
    | AutomationCondition.any_deps_match(
        AutomationCondition.newly_updated() | AutomationCondition.will_be_requested()
    ).with_label("any parents updated")
)

allow_outdated_and_missing_parents_condition = (
    AutomationCondition.in_latest_time_window()
    & became_missing_or_any_parents_updated.since(
        AutomationCondition.newly_requested() | AutomationCondition.newly_updated()
    )
    & ~AutomationCondition.in_progress()
).with_label(
    "update non-partitioned asset while allowing some missing or outdated parent partitions"
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

        default_metadata = default_metadata_from_dbt_resource_props(dbt_resource_props)

        return {**default_metadata, **metadata}

    def get_automation_condition(self, dbt_resource_props: Mapping[str, Any]):
        if dbt_resource_props["name"] in ["company_stats", "locations_cleaned", "weekly_order_summary", "order_stats"]:
           return allow_outdated_and_missing_parents_condition

        if  dbt_resource_props["name"] in ["sku_stats"]:
            return AutomationCondition.on_cron('0 0 1 * *')
        
        if dbt_resource_props["name"] in ["company_perf"]:
            return AutomationCondition.any_downstream_conditions()

    def get_owners(self, dbt_resource_props: Mapping[str, Any]):
        return [
            dbt_resource_props["group"]["owner"]["email"],
            f"team:{dbt_resource_props['group']['name']}",
        ]

def _process_partitioned_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
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
    backfill_policy=BackfillPolicy.single_run(),
)
def daily_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
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
    backfill_policy=BackfillPolicy.single_run(),
)
def weekly_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from _process_partitioned_dbt_assets(context=context, dbt=dbt)


weekly_freshness_check = build_freshness_checks_from_dbt_assets(
    dbt_assets=[weekly_dbt_assets]
)
weekly_freshness_check_sensor = build_sensor_for_freshness_checks(
    freshness_checks=weekly_freshness_check, name="weekly_freshness_check_sensor"
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
def regular_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
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




# This op will be used to run slim CI
@op(out={})
def dbt_slim_ci(dbt2: DbtCliResource):
    dbt_command = [
        "build",
        "--select",
        "state:modified.body+",
        "--defer",
        "--state",
        dbt2.state_path,
    ]

    yield from (
        dbt2.cli(
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
@job
def dbt_slim_ci_job():
    dbt_slim_ci()


# Load and parse the dbt manifest
def load_dbt_manifest(manifest_path):
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    return manifest

# Create AssetCheckSpec objects from the dbt manifest
def create_source_freshness_check_specs(manifest_path):
    manifest = load_dbt_manifest(manifest_path)
    check_specs = []
    for _, source_data in manifest['sources'].items():
        freshness = source_data.get("freshness")
        if freshness and freshness.get("error_after", {}).get("count") is not None:
            asset_key = AssetKey([source_data["schema"].upper(), source_data["name"] ])
            check_specs.append(
                AssetCheckSpec(
                    name="source_freshness_check",
                    asset=asset_key,
                    blocking=True,            
                    )
        )
    return check_specs

@multi_asset_check(
    specs=create_source_freshness_check_specs(dbt_project.manifest_path),
    can_subset=True,
    required_resource_keys={"dbt"},
)
def source_freshness_check(context: AssetCheckExecutionContext):
    dbt_resource = context.resources.dbt

    selection_list = [f"source:{asset_check_key.asset_key.path[0].lower()}.{asset_check_key.asset_key.path[1]}" for asset_check_key in context.selected_asset_check_keys]
    selection_string = " ".join(selection_list)

    context.log.info(f"Running check source_freshness_check on assets {selection_string}")
    dbt_cli_invocation = dbt_resource.cli(["source", "freshness", "--select", selection_string], raise_on_error=False)
    # TODO add better metadata
    # Process the raw event stream
    for dbt_event in dbt_cli_invocation.stream_raw_events():
        context.log.info(f"Received event: {dbt_event.raw_event}")
        if dbt_event.raw_event.get('info', {}).get('name') == 'LogFreshnessResult':
            log_freshness_result = dbt_event.raw_event['info']
            context.log.info(f"Filtered LogFreshnessResult: {log_freshness_result}")
            passed = True if log_freshness_result['level'] == 'info' else False
            severity = AssetCheckSeverity.ERROR if log_freshness_result['level'] == 'error' else AssetCheckSeverity.WARN
            yield AssetCheckResult(
                asset_key=AssetKey([dbt_event.raw_event['data']['node_info']['node_relation']['schema'].upper(), dbt_event.raw_event['data']['node_info']['node_name']]),
                check_name="source_freshness_check",
                passed=passed,
                severity=severity,
                metadata={},
            )