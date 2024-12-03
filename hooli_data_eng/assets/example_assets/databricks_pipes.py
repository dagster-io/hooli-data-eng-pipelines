from dagster_databricks import PipesDatabricksClient

from dagster import AssetExecutionContext, asset, MaterializeResult
from databricks.sdk.service import jobs

# This databricks pipes asset only runs in prod, see utils/external_databricks_script.py
# The dependency on predicted_orders is not a real dependency since the script does not rely
# or use that upstream Snowflake table, it is used here for illustrative purposes
@asset(
    kinds={"pyspark", "databricks"},
    group_name="DEMO_EXAMPLES"
)
def my_databricks_asset(
    context: AssetExecutionContext,
    pipes_databricks_client: PipesDatabricksClient,
) -> MaterializeResult:
    # cluster config
    cluster_config = {
        "num_workers": 1,
        "spark_version": "11.2.x-scala2.12",
        "node_type_id": "i3.xlarge",
    }

    # task specification will be passed to Databricks as-is, except for the
    # injection of environment variables
    task = jobs.SubmitTask.from_dict(
        {
            "new_cluster": cluster_config,
            "libraries": [
                # must include dagster-pipes
                {"pypi": {"package": "beautifulsoup4"}},
                {"pypi": {"package": "dagster-pipes"}},
                {"pypi": {"package": "html5lib"}},
                {"pypi": {"package": "pandas"}},
                {"pypi": {"package": "scikit-learn"}},
            ],
            "task_key": "dagster-launched",
            "spark_python_task": {
                "python_file": "dbfs:/FileStore/my_pipes_examples/my_external_databricks_script.py",
                "source": jobs.Source.WORKSPACE,
            },
        }
    )

    # synchronously execute the databricks job
    return pipes_databricks_client.run(
        task=task,
        context=context,
    ).get_materialize_result()