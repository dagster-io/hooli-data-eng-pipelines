import json
import os
import requests
import dagster as dg
from dagster_dbt import DbtCliResource
from hooli_data_eng.defs.dbt.resources import dbt_project, resource_def
from hooli_data_eng.defs.dbt.translator import get_hooli_translator
from hooli_data_eng.utils import get_env


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

            # Yield all the events from dbt
            for event in (
                dbt_cli_task
                .stream()
                .fetch_row_counts()
                .fetch_column_metadata()
            ):
                yield event
            
            # Get run results and return as JSON string
            try:
                run_results = dbt_cli_task.get_artifact("run_results.json")
                context.log.info(f"dbt completed with {len(run_results.get('results', []))} model results")
                yield dg.Output(json.dumps(run_results), "run_results")
            except Exception as e:
                context.log.warning(f"Could not retrieve run_results.json: {str(e)}")
                # Return basic success info if we can't get detailed results
                yield dg.Output(json.dumps({
                    "status": "completed", 
                    "results": [], 
                    "message": "dbt completed but detailed results not available"
                }), "run_results")
                
        except Exception as e:
            context.log.error(f"dbt slim CI failed: {str(e)}")
            # Return error info so the GitHub comment can still be posted
            yield dg.Output(json.dumps({
                "error": str(e), 
                "status": "failed",
                "message": f"dbt slim CI job failed with error: {str(e)}"
            }), "run_results")

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


# Create the slim CI definitions with the correct resource reference
slim_ci_defs = dg.Definitions(
    jobs=[get_slim_ci_job()],
    resources=resource_def[get_env()],
)
