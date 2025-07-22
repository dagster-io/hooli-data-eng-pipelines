import dagster as dg
from typing import List, Dict, Any, Optional
from pydantic import field_validator
from hooli_ml.defs.resources import DatabricksResource


class NotebookTaskConfig(dg.Config):
    """Config for overriding parameters for a specific notebook task."""
    parameters: Dict[str, Any] = {}


class MultiNotebookJobConfig(dg.Config):
    """Config for overriding parameters for notebook tasks by asset key."""
    asset_configs: Dict[str, NotebookTaskConfig] = {}


class DatabricksMultiNotebookJobComponent(dg.Component, dg.Model, dg.Resolvable):
    """
    A Databricks component that runs multiple notebooks as tasks in a single Databricks job.
    
    This component creates a multi-asset that submits all notebook tasks as a single job,
    allowing for better resource utilization and coordination between related tasks.
    """
    
    job_name_prefix: str = "dagster_multi_notebook_job"
    
    # Serverless configuration
    serverless: bool = False
    
    # Cluster configuration fields (optional when serverless=True)
    spark_version: Optional[str] = "13.3.x-scala2.12"
    node_type_id: Optional[str] = "i3.xlarge"
    num_workers: Optional[int] = 1
    
    # Task configuration with embedded asset specs
    tasks: List[Dict[str, Any]]
    
    @field_validator('spark_version', 'node_type_id', 'num_workers')
    @classmethod
    def validate_cluster_fields(cls, v, info):
        """Validate that cluster fields are provided when not using serverless."""
        if info.data.get('serverless', False):
            # When serverless=True, these fields are optional
            return v
        else:
            # When serverless=False, these fields are required
            if v is None:
                field_name = info.field_name
                raise ValueError(f"{field_name} is required when serverless=False")
            return v
    
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        from databricks.sdk.service import jobs
        
        # Create asset specs from task definitions
        asset_specs = []
        for task in self.tasks:
            task_key = task["task_key"]
            asset_specs_config = task.get("asset_specs", [])
            
            # If no asset_specs defined, create a default one from task_key
            if not asset_specs_config:
                asset_specs_config = [{}]  # Single empty spec that will use defaults
            
            # Process each asset spec for this task
            for asset_spec_config in asset_specs_config:
                # Extract asset spec properties with defaults
                asset_key = asset_spec_config.get("key", task_key)
                description = asset_spec_config.get("description", f"Asset for task {task_key}")
                kinds = set(asset_spec_config.get("kinds", ["databricks"]))  # Default to databricks
                skippable = asset_spec_config.get("skippable", True)  # Default to True
                deps = asset_spec_config.get("deps", [])  # Default to no dependencies
                
                # Convert deps to AssetKey objects if they are strings
                deps_keys = []
                for dep in deps:
                    if isinstance(dep, str):
                        deps_keys.append(dg.AssetKey(dep))
                    else:
                        deps_keys.append(dep)  # Assume it's already an AssetKey
                
                asset_specs.append(dg.AssetSpec(
                    key=asset_key,
                    description=description,
                    kinds=kinds,
                    skippable=skippable,
                    deps=deps_keys,
                ))
        
        @dg.multi_asset(name=f"{self.job_name_prefix}_multi_asset", specs=asset_specs, can_subset=True)
        def multi_notebook_job_asset(
            context: dg.AssetExecutionContext, 
            databricks_resource: DatabricksResource,
            config: MultiNotebookJobConfig
        ):
            """Multi-asset that runs multiple notebooks as a single Databricks job."""
            
            # Get selected asset keys that are being materialized
            selected_assets = context.selected_asset_keys
            context.log.info(f"Selected assets: {selected_assets}")
            
            # Filter tasks to only include those that correspond to selected assets
            selected_tasks = []
            
            for task in self.tasks:
                task_key = task["task_key"]
                asset_specs_config = task.get("asset_specs", [{}])  # Default to single empty spec
                
                # Check if any of this task's asset specs are selected
                task_has_selected_assets = False
                for asset_spec_config in asset_specs_config:
                    asset_key = asset_spec_config.get("key", task_key)
                    if dg.AssetKey(asset_key) in selected_assets:
                        task_has_selected_assets = True
                        context.log.info(f"Task {task_key} with asset_key {asset_key} is selected")
                        break
                
                if task_has_selected_assets:
                    selected_tasks.append(task)
                else:
                    context.log.info(f"Task {task_key} is NOT selected (no asset specs selected)")
            
            context.log.info(f"Running {len(selected_tasks)} out of {len(self.tasks)} tasks")
            
            # Only proceed if we have selected tasks
            if not selected_tasks:
                context.log.info("No tasks selected for execution")
                return
            
            # Create Databricks SDK task objects only for selected tasks
            databricks_tasks = []
            for task in selected_tasks:
                task_key = task["task_key"]
                
                # Get base parameters from task definition
                base_parameters = task.get("parameters", {})
                
                # For config overrides, we need to determine which asset keys correspond to this task
                # and merge config from all of them
                asset_specs_config = task.get("asset_specs", [{}])  # Default to single empty spec
                merged_config_parameters = {}
                
                for asset_spec_config in asset_specs_config:
                    asset_key = asset_spec_config.get("key", task_key)
                    asset_key_str = str(asset_key)
                    
                    # Get config overrides for this asset (if any)
                    asset_config = config.asset_configs.get(asset_key_str)
                    if asset_config:
                        # Merge config parameters from all asset specs for this task
                        merged_config_parameters.update(asset_config.parameters)
                
                # Merge base parameters with config overrides (config overrides take precedence)
                final_parameters = {**base_parameters, **merged_config_parameters}
                
                context.log.info(f"Task {task_key}: base_parameters={base_parameters}, config_overrides={merged_config_parameters}, final_parameters={final_parameters}")
                
                # Configure cluster based on serverless setting
                if self.serverless:
                    cluster_spec = {}
                else:
                    cluster_spec = jobs.ClusterSpec(
                        spark_version=self.spark_version,
                        node_type_id=self.node_type_id,
                        num_workers=self.num_workers
                    )
                
                databricks_task = jobs.SubmitTask(
                    task_key=task_key,
                    notebook_task=jobs.NotebookTask(
                        notebook_path=task["notebook_path"],
                        base_parameters=final_parameters  # Use merged parameters
                    ),
                    new_cluster=cluster_spec
                )
                databricks_tasks.append(databricks_task)
            
            # Submit the job with only selected tasks
            client = databricks_resource.workspace_client()
            job_run = client.jobs.submit(
                run_name=f"{self.job_name_prefix}_{context.run_id}",
                tasks=databricks_tasks
            )
            
            context.log.info(f"Submitted Databricks job with run ID: {job_run.run_id}")
            
            # Wait for job completion
            client.jobs.wait_get_run_job_terminated_or_skipped(job_run.run_id)
            
            # Get final job status
            final_run = client.jobs.get_run(job_run.run_id)
            
            if final_run.state.result_state.value == "SUCCESS":
                context.log.info(f"All {len(selected_tasks)} selected notebook tasks completed successfully")
                
                # Yield MaterializeResult for each asset produced by the selected tasks
                for task in selected_tasks:
                    task_key = task["task_key"]
                    asset_specs_config = task.get("asset_specs", [{}])  # Default to single empty spec
                    base_parameters = task.get("parameters", {})
                    
                    # Yield a result for each asset spec defined for this task
                    for asset_spec_config in asset_specs_config:
                        asset_key = asset_spec_config.get("key", task_key)
                        asset_key_str = str(asset_key)
                        
                        # Get config info for metadata for this specific asset
                        asset_config = config.asset_configs.get(asset_key_str)
                        config_overrides = asset_config.parameters if asset_config else {}
                        final_parameters = {**base_parameters, **config_overrides}
                        
                        yield dg.MaterializeResult(
                            asset_key=asset_key,
                            metadata={
                                "job_run_id": job_run.run_id,
                                "task_key": task_key,
                                "notebook_path": task["notebook_path"],
                                "serverless": self.serverless,
                                "executed_in_subset": True,
                                "total_tasks_in_job": len(selected_tasks),
                                "status": "completed",
                                "base_parameters": base_parameters,
                                "config_overrides": config_overrides,
                                "final_parameters": final_parameters,
                                "has_config_overrides": bool(config_overrides),
                                "asset_spec_defaults_applied": {
                                    "skippable": asset_spec_config.get("skippable", True),
                                    "kinds": asset_spec_config.get("kinds", ["databricks"])
                                }
                            }
                        )
            else:
                raise Exception(f"Job failed with state: {final_run.state.result_state}")
        
        return dg.Definitions(assets=[multi_notebook_job_asset])
