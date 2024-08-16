from dagster_databricks import PipesDatabricksClient

from dagster import AssetExecutionContext, asset
from databricks.sdk.service import jobs

# This databricks pipes asset only runs in prod, see utils/external_databricks_script.py
# The dependency on predicted_orders is not a real dependency since the script does not rely
# or use that upstream Snowflake table, it is used here for illustrative purposes
@asset(
    deps=[predicted_orders],
    compute_kind="databricks",
    tags={**StorageKindTagSet(storage_kind="databricks")},
)
def databricks_asset(
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
                {"pypi": {"package": "dagster-pipes"}},
            ],
            "task_key": "dagster-launched",
            "spark_python_task": {
                "python_file": "dbfs:/FileStore/external_databricks_script.py",
                "source": jobs.Source.WORKSPACE,
            },
        }
    )

    # Arbitrary json-serializable data you want access to from the `PipesSession`
    # in the Databricks runtime. Assume `sample_rate` is a parameter used by
    # the target job's business logic.
    extras = {"sample_rate": 1.0}

    # synchronously execute the databricks job
    return pipes_databricks_client.run(
        task=task,
        context=context,
        extras=extras,
    ).get_materialize_result()