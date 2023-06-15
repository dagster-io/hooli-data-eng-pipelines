
from typing import Any, Mapping
from dagster._utils import file_relative_path
from dagster_dbt import load_assets_from_dbt_project
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.cli import DbtCli, DbtManifest
from dagster import AssetKey, DailyPartitionsDefinition, WeeklyPartitionsDefinition, OpExecutionContext, Output
from dateutil import parser
import json 

# many dbt assets use an incremental approach to avoid
# re-processing all data on each run
# this approach can be modelled in dagster using partitions 
# this project includes assets with hourly and daily partitions
daily_partitions = DailyPartitionsDefinition(start_date="2023-05-25")
weekly_partitions = WeeklyPartitionsDefinition(start_date="2023-05-25")

DBT_PROJECT_DIR = file_relative_path(__file__, "../../dbt_project")
DBT_PROFILES_DIR = file_relative_path(__file__, "../../dbt_project/config")


DBT_MANIFEST = file_relative_path(__file__, "../../target/manifest.json")

class CustomizedDbtManifest(DbtManifest):

    @classmethod
    def node_info_to_metadata(cls, node_info: Mapping[str, Any]) -> Mapping[str, Any]:
            metadata = {"partition_expr": "orders_date"}
           
            if node_info['name'] == 'orders_cleaned':
                metadata = {"partition_expr": "dt"}
            
            if node_info['name'] == 'users_cleaned':
                metadata = {"partition_expr": "created_at"}

            return metadata   

    @classmethod
    def node_info_to_asset_key(cls, node_info: Mapping[str, Any]) -> AssetKey:
        
        node_path = node_info['path']
        prefix = node_path.split('/')[0]
        
        if node_path == 'models/sources.yml':
            prefix = "RAW_DATA"
        
        return AssetKey([prefix, node_info['name']])
    
    @classmethod
    def node_info_to_description(cls, node_info: Mapping[str, Any]) -> str:
        description_sections = []

        description = node_info.get("description", "")
        if description:
            description_sections.append(description)

        raw_code = node_info.get("raw_code", "")
        if raw_code:
            description_sections.append(f"#### Raw SQL:\n```\n{raw_code}\n```")

        return "\n\n".join(description_sections)

manifest = CustomizedDbtManifest.read(path=DBT_MANIFEST)

def _process_partitioned_dbt_assets(context: OpExecutionContext, dbt2: DbtCli):
     # map partition key range to dbt vars
    first_partition, last_partition = context.asset_partitions_time_window_for_output(list(context.selected_output_names)[0])
    dbt_vars = {"min_date": str(first_partition), "max_date": str(last_partition)}
    dbt_args = ["run", "--vars", json.dumps(dbt_vars)]

    dbt_cli_task = dbt2.cli(dbt_args, manifest=manifest, context=context)

    dbt_events = list(dbt_cli_task.stream_raw_events())

    for event in dbt_events:
        # add custom metadata to the asset materialization event 
        context.log.info(event)
        for dagster_event in event.to_default_asset_events(manifest=manifest):
            
            if isinstance(dagster_event, Output):
                event_node_info = event.event["data"]["node_info"]

                started_at = parser.isoparse(event_node_info["node_started_at"])
                completed_at = parser.isoparse(event_node_info["node_finished_at"])

                metadata = {
                    "Execution Started At": started_at.isoformat(timespec="seconds"),
                    "Execution Completed At": completed_at.isoformat(timespec="seconds"),
                    "Execution Duration": (completed_at - started_at).total_seconds(),
                    "Owner": "data@hooli.com"
                }

                context.add_output_metadata(
                    metadata=metadata,
                    output_name=dagster_event.output_name,
                )

            yield dagster_event
    
    if not dbt_cli_task.is_successful():
        raise Exception('dbt command failed, see preceding events')
    

@dbt_assets(
        manifest=manifest,
        select="orders_cleaned users_cleaned orders_augmented", 
        partitions_def=daily_partitions,
)
def daily_dbt_assets(context: OpExecutionContext, dbt2: DbtCli):
    yield from _process_partitioned_dbt_assets(context=context, dbt2=dbt2)

@dbt_assets(
        manifest=manifest,
        select="weekly_order_summary order_stats", 
        partitions_def=weekly_partitions
)
def weekly_dbt_assets(context: OpExecutionContext, dbt2: DbtCli):
    yield from _process_partitioned_dbt_assets(context=context, dbt2=dbt2)


dbt_views = load_assets_from_dbt_project(
    DBT_PROJECT_DIR,
    DBT_PROFILES_DIR,
    key_prefix=["ANALYTICS"],
    source_key_prefix="ANALYTICS",
    select="company_perf sku_stats company_stats"
)



