import json
import os
from typing import Any, Mapping, Union, Literal, Optional
import dagster as dg
from hooli_data_eng.utils import get_env
from dagster_dbt import DbtCliResource
from hooli_data_eng.defs.dbt.resources import dbt_project
from hooli_data_eng.defs.dbt.component import get_hooli_translator
from github import Github


@dg.op(out={})
def dbt_slim_ci(context: dg.OpExecutionContext, dbt: DbtCliResource):
    """Run dbt slim CI and post GitHub comment with successful models"""
    dbt_command = [
        "build",
        "--select",
        "state:modified.body+",
        "--defer",
        "--state",
        dbt.state_path,
    ]

    dbt_cli_task = dbt.cli(
        args=dbt_command,
        manifest=dbt_project.manifest_path,
        dagster_dbt_translator=get_hooli_translator(),
    )

    # Collect results and track successful models
    successful_models = []
    
    for event in dbt_cli_task.stream().fetch_row_counts().fetch_column_metadata():
        yield event
        
    # Get run results to identify successful models
    try:
        run_results_json = dbt_cli_task.get_artifact("run_results.json")
        for result in run_results_json.get("results", []):
            if result.get("status") == "success":
                model_name = result.get("unique_id", "").split(".")[-1]
                if model_name:
                    successful_models.append(model_name)
                    
        context.log.info(f"Successfully ran {len(successful_models)} dbt models: {successful_models}")
        
        # Post GitHub comment if in CI environment
        _post_github_comment(context, successful_models)
        
    except Exception as e:
        context.log.warning(f"Could not parse run results or post GitHub comment: {e}")


def _post_github_comment(context: dg.OpExecutionContext, successful_models: list):
    """Post a comment to the GitHub PR about successful dbt models"""
    # Only post comments in CI/branch environment
    if get_env() != "BRANCH":
        context.log.info("Not in branch environment, skipping GitHub comment")
        return
        
    # Get GitHub token and repo info from environment
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPOSITORY")  # format: owner/repo - available by default
    
    # Get PR number from GitHub event (available in pull_request events)
    github_event_path = os.getenv("GITHUB_EVENT_PATH")
    github_pr_number = None
    
    if github_event_path:
        try:
            with open(github_event_path, 'r') as f:
                event_data = json.load(f)
                github_pr_number = event_data.get("number") or event_data.get("pull_request", {}).get("number")
        except Exception as e:
            context.log.warning(f"Could not parse GitHub event data: {e}")
    
    # Fallback to GITHUB_REF for PR number extraction
    if not github_pr_number:
        github_ref = os.getenv("GITHUB_REF")  # format: refs/pull/{pr_number}/merge
        if github_ref and github_ref.startswith("refs/pull/") and github_ref.endswith("/merge"):
            try:
                github_pr_number = int(github_ref.split("/")[2])
            except (IndexError, ValueError):
                pass
    
    if not all([github_token, github_repo, github_pr_number]):
        context.log.warning(
            f"Missing required GitHub information. "
            f"Token: {'✓' if github_token else '✗'}, "
            f"Repo: {'✓' if github_repo else '✗'}, "
            f"PR: {'✓' if github_pr_number else '✗'}. "
            "Cannot post comment."
        )
        return
        
    try:
        g = Github(github_token)
        repo = g.get_repo(github_repo)
        pr = repo.get_pull(int(github_pr_number))
        
        if not successful_models:
            comment_body = "✅ **dbt Slim CI Results**\n\nNo dbt models were modified or ran successfully in this PR."
        else:
            model_list = "\n".join([f"- `{model}`" for model in sorted(successful_models)])
            comment_body = f"""✅ **dbt Slim CI Results**

Successfully ran **{len(successful_models)}** dbt model(s):

{model_list}

All models passed validation and tests!"""
        
        pr.create_issue_comment(comment_body)
        context.log.info(f"Posted GitHub comment to PR #{github_pr_number}")
        
    except Exception as e:
        context.log.error(f"Failed to post GitHub comment: {e}")


@dg.job(name="dbt_slim_ci_with_github_job")
def dbt_slim_ci_with_github_job():
    """Job that runs dbt slim CI and posts GitHub comments"""
    dbt_slim_ci()