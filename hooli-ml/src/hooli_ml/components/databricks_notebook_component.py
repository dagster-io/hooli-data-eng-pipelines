import dagster as dg
from typing import List, Dict, Any, Optional
from pydantic import field_validator
from hooli_ml.defs.resources import DatabricksResource

class DatabricksNotebookComponent(dg.Component, dg.Model, dg.Resolvable):
    # ...existing code...
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        # ...existing code...
        return dg.Definitions()

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
    
    # Task configuration - list of dictionaries with task definitions
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
        
        # Create asset specs for each task
        asset_specs = []
        for task in self.tasks:
            asset_key = task.get("asset_key", task["task_key"])
            kinds = set(task.get("kinds", ["databricks"]))
            asset_specs.append(dg.AssetSpec(
                key=asset_key,
                kinds=kinds,
                skippable=True,
            ))
        
        @dg.multi_asset(specs=asset_specs, can_subset=True)
        def multi_notebook_job_asset(context: dg.AssetExecutionContext, databricks_resource: DatabricksResource):
            """Multi-asset that runs multiple notebooks as a single Databricks job."""
            
            # Get selected output names (asset keys that are being materialized)
            selected_outputs = context.selected_output_names
            context.log.info(f"Selected outputs: {selected_outputs}")
            context.log.info(f"All available outputs: {[spec.key for spec in asset_specs]}")
            
            # Filter tasks to only include those that correspond to selected assets
            selected_tasks = []
            for task in self.tasks:
                asset_key = task.get("asset_key", task["task_key"])
                context.log.info(f"Checking task with asset_key: {asset_key}")
                if asset_key in selected_outputs:
                    selected_tasks.append(task)
                    context.log.info(f"Task {task['task_key']} with asset_key {asset_key} is selected")
                else:
                    context.log.info(f"Task {task['task_key']} with asset_key {asset_key} is NOT selected")
            
            context.log.info(f"Running {len(selected_tasks)} out of {len(self.tasks)} tasks")
            
            # Only proceed if we have selected tasks
            if not selected_tasks:
                context.log.info("No tasks selected for execution")
                return
            
            # Create Databricks SDK task objects only for selected tasks
            databricks_tasks = []
            for task in selected_tasks:
                # Configure cluster based on serverless setting
                if self.serverless:
                    cluster_spec = jobs.ClusterSpec(serverless=True)
                else:
                    cluster_spec = jobs.ClusterSpec(
                        spark_version=self.spark_version,
                        node_type_id=self.node_type_id,
                        num_workers=self.num_workers
                    )
                
                databricks_task = jobs.SubmitTask(
                    task_key=task["task_key"],
                    notebook_task=jobs.NotebookTask(
                        notebook_path=task["notebook_path"],
                        base_parameters=task.get("parameters", {})
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
                
                # Report materialization for ALL assets in the spec, but mark which ones were actually executed
                for task in self.tasks:
                    asset_key = task.get("asset_key", task["task_key"])
                    
                    if asset_key in selected_outputs:
                        # This asset was selected and executed
                        context.log.info(f"Yielding MaterializeResult for EXECUTED asset: {asset_key}")
                        yield dg.MaterializeResult(
                            asset_key=asset_key,
                            metadata={
                                "job_run_id": job_run.run_id,
                                "task_key": task["task_key"],
                                "notebook_path": task["notebook_path"],
                                "serverless": self.serverless,
                                "executed_in_subset": True,
                                "total_tasks_in_job": len(selected_tasks),
                                "status": "completed"
                            }
                        )
                    else:
                        # This asset was NOT selected, yield a result but mark it as skipped
                        context.log.info(f"Yielding MaterializeResult for SKIPPED asset: {asset_key}")
                        yield dg.MaterializeResult(
                            asset_key=asset_key,
                            metadata={
                                "task_key": task["task_key"],
                                "notebook_path": task["notebook_path"],
                                "serverless": self.serverless,
                                "executed_in_subset": False,
                                "skipped_reason": "not selected in subset",
                                "status": "skipped"
                            }
                        )
            else:
                raise Exception(f"Job failed with state: {final_run.state.result_state}")
        
        return dg.Definitions(assets=[multi_notebook_job_asset])
