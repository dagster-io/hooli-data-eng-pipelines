import json
import textwrap
import os
import requests
from typing import Any, Mapping, Union, Literal, Optional
import dagster as dg
from hooli_data_eng.utils import get_env
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
from datetime import datetime
from hooli_data_eng.defs.dbt.dbt_code_version import get_current_dbt_code_version
from hooli_data_eng.defs.dbt.resources import resource_def

from datetime import timedelta
from dagster.preview.freshness import apply_freshness_policy
from dagster.preview.freshness import FreshnessPolicy

# many dbt assets use an incremental approach to avoid
# re-processing all data on each run
# this approach can be modelled in dagster using partitions
# this project includes assets with hourly and daily partitions
daily_partitions = dg.DailyPartitionsDefinition(start_date="2023-05-25")
weekly_partitions = dg.WeeklyPartitionsDefinition(start_date="2023-05-25")


def get_allow_outdated_and_missing_parents_condition():
    became_missing_or_any_parents_updated = (
        dg.AutomationCondition.missing().newly_true().with_label("became missing")
        | dg.AutomationCondition.any_deps_match(
            dg.AutomationCondition.newly_updated()
            | dg.AutomationCondition.will_be_requested()
        ).with_label("any parents updated")
    )

    return (
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
            return get_allow_outdated_and_missing_parents_condition()

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


def get_hooli_translator():
    return CustomDagsterDbtTranslator(
        settings=DagsterDbtTranslatorSettings(
            enable_asset_checks=True,
            enable_code_references=True,
        )
    )


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


def get_slim_ci_job():
    # This op will be used to run slim CI
    @dg.op(out={"run_results": dg.Out(str, description="JSON string of dbt run results")})
    def dbt_slim_ci(context: dg.OpExecutionContext, dbt: DbtCliResource):
        dbt_command = [
            "build",
            "--select",
            "state:modified.body+",
            "--defer",
            "--state",
            dbt.state_path,
        ]

        try:
            dbt_cli_task = dbt.cli(
                args=dbt_command,
                manifest=dbt_project.manifest_path,
                dagster_dbt_translator=get_hooli_translator(),
            )

            yield from (
                dbt_cli_task
                .stream()
                .fetch_row_counts()
                .fetch_column_metadata()
            )
            
            # Get run results and return as JSON string
            try:
                run_results = dbt_cli_task.get_artifact("run_results.json")
                context.log.info(f"dbt completed with {len(run_results.get('results', []))} model results")
                return json.dumps(run_results)
            except Exception as e:
                context.log.warning(f"Could not retrieve run_results.json: {str(e)}")
                # Return basic success info if we can't get detailed results
                return json.dumps({
                    "status": "completed", 
                    "results": [], 
                    "message": "dbt completed but detailed results not available"
                })
                
        except Exception as e:
            context.log.error(f"dbt slim CI failed: {str(e)}")
            # Return error info so the GitHub comment can still be posted
            return json.dumps({
                "error": str(e), 
                "status": "failed",
                "message": f"dbt slim CI job failed with error: {str(e)}"
            })

    # This op will post a comment to GitHub with the dbt results
    @dg.op(ins={"run_results": dg.In(str)})
    def post_github_comment(context: dg.OpExecutionContext, run_results: str):
        """Post a comment to GitHub with dbt run results."""
        
        context.log.info("Starting GitHub comment operation")
        context.log.info(f"Available environment variables: GITHUB_TOKEN={'***' if os.getenv('GITHUB_TOKEN') else 'None'}, "
                        f"DAGSTER_GITHUB_TOKEN={'***' if os.getenv('DAGSTER_GITHUB_TOKEN') else 'None'}, "
                        f"GITHUB_REPOSITORY={os.getenv('GITHUB_REPOSITORY') or 'None'}, "
                        f"DAGSTER_GITHUB_REPOSITORY={os.getenv('DAGSTER_GITHUB_REPOSITORY') or 'None'}, "
                        f"GITHUB_PR_NUMBER={os.getenv('GITHUB_PR_NUMBER') or 'None'}, "
                        f"DAGSTER_GITHUB_PR_NUMBER={os.getenv('DAGSTER_GITHUB_PR_NUMBER') or 'None'}")
        
        # Get configuration from environment variables
        github_token = (
            os.getenv("GITHUB_TOKEN") or
            os.getenv("DAGSTER_GITHUB_TOKEN")
        )
        github_repo = (
            os.getenv("GITHUB_REPOSITORY") or
            os.getenv("DAGSTER_GITHUB_REPOSITORY")
        )
        pr_number = (
            os.getenv("GITHUB_PR_NUMBER") or
            os.getenv("DAGSTER_GITHUB_PR_NUMBER")
        )
        
        if not github_token:
            context.log.info("No GitHub token provided - GitHub commenting is disabled")
            context.log.info("To enable GitHub comments, set GITHUB_TOKEN environment variable")
            return
            
        if not github_repo:
            context.log.info("No GitHub repository provided - GitHub commenting is disabled")
            context.log.info("To enable GitHub comments, set GITHUB_REPOSITORY environment variable")
            return
            
        if not pr_number:
            context.log.info("No PR number provided - GitHub commenting is disabled")
            context.log.info("This is likely because the job is not running in a PR context")
            return

        context.log.info(f"Posting GitHub comment to {github_repo} PR #{pr_number}")

        try:
            results = json.loads(run_results)
            
            # Get Dagster run information for linking
            run_id = context.run_id
            dagster_cloud_deployment = os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "unknown")
            dagster_cloud_org = os.getenv("DAGSTER_CLOUD_ORGANIZATION", "hooli")
            
            # Build Dagster Cloud URL if available
            dagster_url = ""
            if dagster_cloud_org and dagster_cloud_deployment and run_id:
                dagster_url = f"https://{dagster_cloud_org}.dagster.cloud/{dagster_cloud_deployment}/runs/{run_id}"
            
            # Check if there was an error
            if "error" in results:
                comment_body = f"""## ❌ dbt Slim CI Failed

**Error:** {results['error']}

The dbt slim CI job encountered an error during execution. Please check the [Dagster logs]({dagster_url}) for more details.

---
*Generated by Dagster dbt Slim CI* | Run ID: `{run_id}`
"""
            else:
                # Parse successful results
                successful_models = []
                failed_models = []
                total_elapsed_time = results.get("elapsed_time", 0)
                
                for result in results.get("results", []):
                    model_name = result.get("unique_id", "unknown")
                    status = result.get("status", "unknown")
                    execution_time = result.get("execution_time", 0)
                    
                    if status == "success":
                        successful_models.append({
                            "name": model_name,
                            "execution_time": execution_time
                        })
                    else:
                        failed_models.append({
                            "name": model_name,
                            "status": status,
                            "message": result.get("message", "No error message"),
                            "execution_time": execution_time
                        })
                
                if failed_models:
                    comment_body = f"""## ❌ dbt Slim CI Completed with Failures

### ✅ Successful Models ({len(successful_models)})
"""
                    if successful_models:
                        for model in successful_models:
                            execution_time_str = f" ({model['execution_time']:.2f}s)" if model['execution_time'] else ""
                            comment_body += f"- `{model['name']}`{execution_time_str}\n"
                    else:
                        comment_body += "None\n"
                    
                    comment_body += f"""
### ❌ Failed Models ({len(failed_models)})
"""
                    for model in failed_models:
                        execution_time_str = f" ({model['execution_time']:.2f}s)" if model['execution_time'] else ""
                        comment_body += f"- `{model['name']}`{execution_time_str} - Status: `{model['status']}`\n"
                        if model['message']:
                            comment_body += f"  - Error: {model['message']}\n"
                
                else:
                    comment_body = f"""## ✅ dbt Slim CI Successful

All dbt models ran successfully! 

### Models Updated ({len(successful_models)})
"""
                    if successful_models:
                        for model in successful_models:
                            execution_time_str = f" ({model['execution_time']:.2f}s)" if model['execution_time'] else ""
                            comment_body += f"- `{model['name']}`{execution_time_str}\n"
                    else:
                        comment_body += "No models were updated (no changes detected).\n"

                # Add execution summary
                if total_elapsed_time:
                    comment_body += f"\n**Total execution time:** {total_elapsed_time:.2f} seconds\n"

            # Add footer with links
            comment_body += """
---
*Generated by Dagster dbt Slim CI*"""
            
            if dagster_url:
                comment_body += f" | [View Run Details]({dagster_url})"
                
            comment_body += f" | Run ID: `{run_id}`"

            # Post comment to GitHub
            url = f"https://api.github.com/repos/{github_repo}/issues/{pr_number}/comments"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            data = {"body": comment_body}
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 201:
                context.log.info(f"Successfully posted GitHub comment for PR #{pr_number}")
            else:
                context.log.error(f"Failed to post GitHub comment: {response.status_code} - {response.text}")
                
        except Exception as e:
            context.log.error(f"Error posting GitHub comment: {str(e)}")

    # This job will be triggered by Pull Request and should only run new or changed dbt models
    @dg.job
    def dbt_slim_ci_job():
        results = dbt_slim_ci()
        post_github_comment(results)

    return dbt_slim_ci_job
