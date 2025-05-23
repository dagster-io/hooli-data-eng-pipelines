import pandas as pd
import dagster as dg

from dagster_databricks import PipesDatabricksClient
from databricks.sdk.service import jobs
from hooli_data_eng.databricks.resources import launch_and_poll_databricks_job


# This asset uses the forecasted orders to flag any days that
# surpass available capacity
# The asset uses spark which requires a pyspark resource
# and a step launcher
# Locally the pyspark session runs in a local spark context
# In branch and production, the step launcher is responsible
# for building a databricks cluster
@dg.asset(
    ins={"predicted_orders": dg.AssetIn(key_prefix=["FORECASTING"])},
    key_prefix=["FORECASTING"],
    required_resource_keys={"step_launcher", "pyspark"},
    metadata={"resource_constrained_at": 50},
    kinds={"pyspark", "databricks"},
)
def big_orders(context, predicted_orders: pd.DataFrame):
    """Days where predicted orders surpass our current carrying capacity"""
    df = context.resources.pyspark.spark_session.createDataFrame(predicted_orders)
    return df.where(df.num_orders >= 50).toPandas()


# This databricks pipes asset only runs in prod, see utils/external_databricks_script.py
# The dependency on predicted_orders is not a real dependency since the script does not rely
# or use that upstream Snowflake table, it is used here for illustrative purposes
@dg.asset(
    deps=[dg.AssetKey(["FORECASTING", "predicted_orders"])],
    kinds={"pyspark", "databricks"},
)
def databricks_asset(
    context: dg.AssetExecutionContext,
    pipes_databricks_client: PipesDatabricksClient,
) -> dg.MaterializeResult:
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


@dg.asset(
    required_resource_keys={"databricks"},
    deps=[dg.AssetKey(["databricks_asset"])],
)
def databricks_workflow_asset(context: dg.AssetExecutionContext) -> None:
    databricks = context.resources.databricks
    launch_and_poll_databricks_job(context, databricks, 733330858351118)
