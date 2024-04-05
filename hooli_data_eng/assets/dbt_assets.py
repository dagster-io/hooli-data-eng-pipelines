import json
import textwrap
import os
from pathlib import Path
from typing import Any, Mapping
from dagster import (
    AutoMaterializePolicy,
    AutoMaterializeRule,
    AssetKey,
    BackfillPolicy,
    DailyPartitionsDefinition,
    job,
    op,
    OpExecutionContext,
    WeeklyPartitionsDefinition,
)
from dagster_cloud.dagster_insights import dbt_with_snowflake_insights
from dagster_dbt import (
    DbtCliResource, 
    DagsterDbtTranslator,
    load_assets_from_dbt_project,
    default_metadata_from_dbt_resource_props,
    DagsterDbtTranslatorSettings,
    DbtArtifacts,
)
from dagster_dbt.asset_decorator import dbt_assets
from dagster._utils import file_relative_path
from hooli_data_eng.resources import get_env

# many dbt assets use an incremental approach to avoid
# re-processing all data on each run
# this approach can be modelled in dagster using partitions
# this project includes assets with hourly and daily partitions
daily_partitions = DailyPartitionsDefinition(start_date="2023-05-25")
weekly_partitions = WeeklyPartitionsDefinition(start_date="2023-05-25")

DBT_PROJECT_DIR = file_relative_path(__file__, "../../dbt_project")
DBT_PROFILES_DIR = file_relative_path(__file__, "../../dbt_project/config")

# new in 1.6.9, DbtArtifacts is an experimental class that creates a manifest on load 
# if DAGSTER_DBT_PARSE_PROJECT_ON_LOAD is present, 
# otherwise it points to the already-built manifest
dbt_artifacts = DbtArtifacts(
    project_dir=DBT_PROJECT_DIR,
    prepare_command=["--quiet",
                     "parse",
                     "--target",
                     get_env(),
                     "--profiles-dir",
                     DBT_PROFILES_DIR],
)
DBT_MANIFEST = dbt_artifacts.manifest_path

# this manifest represents the last successful dbt deployment and will be compared against the current deployment
SLIM_CI_MANIFEST =  Path(
    file_relative_path(__file__, "../../dbt_project/target/slim_ci/")
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

def _process_partitioned_dbt_assets(context: OpExecutionContext, dbt: DbtCliResource):
    # map partition key range to dbt vars
    first_partition, last_partition = context.asset_partitions_time_window_for_output(
        list(context.selected_output_names)[0]
    )
    dbt_vars = {"min_date": str(first_partition), "max_date": str(last_partition)}
    dbt_args = ["build", "--vars", json.dumps(dbt_vars)]

    # Invoke dbt CLI
    dbt_cli_task = dbt.cli(dbt_args, context=context)

    # Emits an AssetObservation for each asset materialization, which is used to 
    # identify the Snowflake credit consumption
    yield from dbt_with_snowflake_insights(context, dbt_cli_task)

    # fetch run_results.json to log compiled SQL
    run_results_json = dbt_cli_task.get_artifact("run_results.json")
    for result in run_results_json["results"]:
        model_name = result.get("unique_id")
        context.log.info(f"Compiled SQL for {model_name}:\n{result['compiled_code']}")


@dbt_assets(
    manifest=DBT_MANIFEST,
    select="orders_cleaned users_cleaned orders_augmented",
    partitions_def=daily_partitions,
    dagster_dbt_translator=CustomDagsterDbtTranslator(settings=DagsterDbtTranslatorSettings(enable_asset_checks=True)),
    backfill_policy=BackfillPolicy.single_run(),
)
def daily_dbt_assets(context: OpExecutionContext, dbt2: DbtCliResource):
    yield from _process_partitioned_dbt_assets(context=context, dbt=dbt2)


@dbt_assets(
    manifest=DBT_MANIFEST,
    select="weekly_order_summary order_stats",
    partitions_def=weekly_partitions,
    dagster_dbt_translator=CustomDagsterDbtTranslator(DagsterDbtTranslatorSettings(enable_asset_checks=True)),
    backfill_policy=BackfillPolicy.single_run(),
)
def weekly_dbt_assets(context: OpExecutionContext, dbt2: DbtCliResource):
    yield from _process_partitioned_dbt_assets(context=context, dbt=dbt2)


dbt_views = load_assets_from_dbt_project(
    DBT_PROJECT_DIR,
    DBT_PROFILES_DIR,
    select="company_perf sku_stats company_stats locations_cleaned",
    dagster_dbt_translator=CustomDagsterDbtTranslatorForViews()
)


# This op will be used to run slim CI
@op(
    out={}
)
def dbt_slim_ci(dbt2: DbtCliResource):
    slim_ci_manifest = SLIM_CI_MANIFEST if SLIM_CI_MANIFEST.exists() else DBT_MANIFEST.parent 

    dbt_command = [
        "build",
        "--select", "state:modified+",
        "--defer",
        "--state", f"{slim_ci_manifest}"
    ]

    yield from dbt2.cli(
        args=dbt_command,
        manifest=DBT_MANIFEST,
        dagster_dbt_translator=CustomDagsterDbtTranslator(DagsterDbtTranslatorSettings(enable_asset_checks=True))
        ).stream()

# This job will be triggered by Pull Request and should only run new or changed dbt models
@job
def dbt_slim_ci_job():
    dbt_slim_ci()