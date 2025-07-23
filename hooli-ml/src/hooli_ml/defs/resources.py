import dagster as dg
import os
import time
import requests
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs

def get_env() -> str:
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "gtm20":
        # PROD
        return 'prod'
    elif os.getenv("DAGSTER_IS_DEV_CLI"):
        # LOCAL
        return 'dev'
    else:
        # BRANCH
        return 'staging'


class MLWorkflowConfig(dg.Config):
    model_type: str = "RandomForest"  # Can be set via config


class DatabricksResource(dg.ConfigurableResource):

    databricks_host: str
    databricks_token: str

    def workspace_client(self) -> WorkspaceClient:
        """Returns a Databricks WorkspaceClient instance."""
        return WorkspaceClient(host=self.databricks_host, token=self.databricks_token)
    
    def run_and_stream_notebook_logs(
        self,
        notebook_path: str,
        parameters: dict = None,
        databricks_host: str = None,
        databricks_token: str = None,
        log_file_path: str = None,  # e.g., '/dbfs/tmp/my_job_log.txt'
    ):
        databricks_host = self.databricks_host
        databricks_token = self.databricks_token
        api_url = f"{databricks_host}/api/2.1/jobs/runs/submit"
        headers = {"Authorization": f"Bearer {databricks_token}"}

        payload = {
            "run_name": "notebook-task",
            "tasks": [
                {
                    "task_key": "notebook-task",
                    "notebook_task": {
                        "notebook_path": notebook_path,
                        "base_parameters": parameters or {},
                    },
                    # "new_cluster": {
                    #     "serverless": True
                    # }
                }
            ]
        }
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        run_id = response.json()["run_id"]
        print(f"Submitted run {run_id}. Polling for completion and streaming logs...")

        last_log = ""
        while True:
            run_info = requests.get(f"{databricks_host}/api/2.1/jobs/runs/get", params={"run_id": run_id}, headers=headers).json()
            state = run_info["state"]
            life_cycle = state["life_cycle_state"]
            result_state = state.get("result_state")
            print(f"Run state: {life_cycle}")
            # Custom log streaming from DBFS file if path is provided
            if log_file_path:
                try:
                    log_response = requests.get(f"{databricks_host}/api/2.0/dbfs/read", headers=headers, params={"path": log_file_path})
                    if log_response.status_code == 200:
                        import base64
                        content = base64.b64decode(log_response.json()["data"]).decode("utf-8")
                        if content != last_log:
                            new_lines = content[len(last_log):]
                            print(new_lines, end="")
                            last_log = content
                except Exception as e:
                    pass  # Ignore errors if log file doesn't exist yet
            if life_cycle in ("TERMINATED", "SKIPPED", "INTERNAL_ERROR"):
                print(f"Run finished with state: {result_state}")
                break
            time.sleep(10)
        return run_id


    def run_and_stream_notebook_logs_sdk(
        self,
        notebook_path: str,
        parameters: dict = None,
        databricks_host: str = None,
        databricks_token: str = None,
    ):
        databricks_host = databricks_host or os.getenv("DATABRICKS_HOST")
        databricks_token = databricks_token or os.getenv("DATABRICKS_TOKEN")
        w = WorkspaceClient(host=databricks_host, token=databricks_token)
        
        run = w.jobs.submit(
            tasks=[
                jobs.SubmitTask(
                    task_key="notebook-task",
                    notebook_task=jobs.NotebookTask(
                        notebook_path=notebook_path,
                        base_parameters=parameters or {},
                    ),
                    #new_cluster=jobs.ClusterSpec(serverless=True),
                )
            ],
            run_name="notebook-task",
        ).result()
        run_id = run.run_id
        output = w.jobs.get_run_output(run_id=run.tasks[0].run_id)
        print(f"Submitted run {run_id}. output: {output}")
        return run_id

@dg.definitions
def resources() -> dg.Definitions:

    resource_defs = {
        
        "databricks_resource": DatabricksResource(
            databricks_host=dg.EnvVar("DATABRICKS_HOST"),
            databricks_token=dg.EnvVar("DATABRICKS_TOKEN")),
    }

    return dg.Definitions(resources=resource_defs)
