from typing import Any, Tuple

import numpy as np
import pandas as pd
from scipy import optimize

from dagster import (
    asset,
    AssetKey,
    AssetIn,
    MonthlyPartitionsDefinition,
    Output,
    Field,
    Config,
    AssetExecutionContext,
    MaterializeResult,
    SourceAsset,
)
from dagster_k8s import PipesK8sClient
from dagstermill import define_dagstermill_asset
from dagster._core.definitions.tags import StorageKindTagSet
from dagster._utils import file_relative_path
from dagster_databricks import PipesDatabricksClient
from databricks.sdk.service import jobs
from pydantic import Field

from hooli_data_eng.utils.storage_kind_helpers import get_storage_kind


# dynamically determine storage_kind based on environment
storage_kind = get_storage_kind()


def model_func(x, a, b):
    return a * np.exp(b * (x / 10**18 - 1.6095))


CONTAINER_REGISTRY = (
    "764506304434.dkr.ecr.us-west-2.amazonaws.com/hooli-data-science-prod"
)

# ----- Forecasting Assets -----
# These assets live downstream of tables created by dbt
# which are referenced by the key_prefix 'analytics',
# but otherwise can be referenced as data frames --
# the IO from the warehouse to these pandas assets are handled
# by the IO Managers

# This asset trains a model and stores the model coefficients as
# a tuple
# The hyper-parameters for the model (a_init and b_init) are
# available as parameters that can be changed in Dagster's
# Launchpad (see config_schema)
# The final model coefficients are logged to Dagster
# using context.log.info


class modelHyperParams(Config):
    """Hyper parameters for the ML model with default values"""

    a_init: float = Field(5, description="initial value for a parameter, intercept")
    b_init: float = Field(5, description="initial value for b parameter, slope")


@asset(
    ins={"weekly_order_summary": AssetIn(key_prefix=["ANALYTICS"])},
    compute_kind="scikitlearn",
    io_manager_key="model_io_manager",
    tags={**StorageKindTagSet(storage_kind="s3")},
)
def order_forecast_model(
    context, weekly_order_summary: pd.DataFrame, config: modelHyperParams
) -> Any:
    """Model parameters that best fit the observed data"""
    df = weekly_order_summary
    p0 = [config.a_init, config.b_init]
    coeffs = tuple(
        optimize.curve_fit(
            f=model_func,
            xdata=df.order_date.astype(np.int64),
            ydata=df.num_orders,
            p0=p0,
        )[0]
    )
    context.log.info("Starting with: " + str(p0[0]) + " and " + str(p0[1]))
    context.log.info("Ended with: " + str(coeffs[0]) + " and " + str(coeffs[1]))
    return coeffs


# This asset uses the data from the warehouse and the trained model
# coefficients to track model error by month
# The monthly error is modelled as a partioned asset to enable
# easy backfills if the error statistic or upstream model change
# Helpful information is surfaced in dagster using the Output(... metadata)
@asset(
    ins={
        "weekly_order_summary": AssetIn(key_prefix=["ANALYTICS"]),
        "order_forecast_model": AssetIn(),
    },
    compute_kind="scikitlearn",
    key_prefix=["forecasting"],
    io_manager_key="model_io_manager",
    partitions_def=MonthlyPartitionsDefinition(start_date="2022-01-01"),
    tags={"core_kpis":"",
          **StorageKindTagSet(storage_kind=storage_kind)},
)
def model_stats_by_month(
    context,
    weekly_order_summary: pd.DataFrame,
    order_forecast_model: Tuple[float, float],
) -> Output[pd.DataFrame]:
    """Model errors by month"""
    a, b = order_forecast_model
    target_date = pd.to_datetime(context.asset_partition_key_for_output())
    target_month = target_date.month
    weekly_order_summary["order_date"] = pd.to_datetime(
        weekly_order_summary["order_date"]
    )
    weekly_order_summary["order_month"] = pd.DatetimeIndex(
        weekly_order_summary["order_date"]
    ).month
    target_orders = weekly_order_summary[
        (weekly_order_summary["order_month"] == target_month)
    ]
    date_range = pd.date_range(
        start=target_date, end=target_date + pd.DateOffset(days=30)
    )
    predicted_orders = model_func(x=date_range.astype(np.int64), a=a, b=b)
    error = sum(target_orders["num_orders"]) - sum(predicted_orders)
    context.log.info("Error for " + str(target_date) + ": " + str(error))

    return Output(pd.DataFrame({"error": [error]}), metadata={"error_obs_prds": error})


# This asset uses the trained model to forecast 30 day forward orders
# and stores the result in the warehouse
@asset(
    ins={
        "weekly_order_summary": AssetIn(key_prefix=["ANALYTICS"]),
        "order_forecast_model": AssetIn(),
    },
    compute_kind="pandas",
    key_prefix=["FORECASTING"],
    tags={**StorageKindTagSet(storage_kind=storage_kind)},
)
def predicted_orders(
    weekly_order_summary: pd.DataFrame, order_forecast_model: Tuple[float, float]
) -> pd.DataFrame:
    """Predicted orders for the next 30 days based on the fit paramters"""
    a, b = order_forecast_model
    start_date = weekly_order_summary.order_date.max()
    future_dates = pd.date_range(
        start=start_date, end=pd.to_datetime(start_date) + pd.DateOffset(days=30)
    )
    predicted_data = model_func(x=future_dates.astype(np.int64), a=a, b=b)
    return pd.DataFrame({"order_date": future_dates, "num_orders": predicted_data})


# This asset uses the forecasted orders to flag any days that
# surpass available capacity
# The asset uses spark which requires a pyspark resource
# and a step launcher
# Locally the pyspark session runs in a local spark context
# In branch and production, the step launcher is responsible
# for building a databricks cluster
@asset(
    ins={"predicted_orders": AssetIn(key_prefix=["FORECASTING"])},
    compute_kind="pyspark",
    key_prefix=["FORECASTING"],
    required_resource_keys={"step_launcher", "pyspark"},
    metadata={"resource_constrained_at": 50},
    tags={**StorageKindTagSet(storage_kind="databricks")},
)
def big_orders(context, predicted_orders: pd.DataFrame):
    """Days where predicted orders surpass our current carrying capacity"""
    df = context.resources.pyspark.spark_session.createDataFrame(predicted_orders)
    return df.where(df.num_orders >= 50).toPandas()


# This asset uses a Jupyter Notebook which takes inputs from the warehouse
# and the trained model coefficients
model_nb = define_dagstermill_asset(
    name="model_nb",
    notebook_path=file_relative_path(__file__, "model.ipynb"),
    ins={
        "weekly_order_summary": AssetIn(
            key_prefix=["ANALYTICS"], dagster_type=pd.DataFrame
        ),
        "order_forecast_model": AssetIn(),
    },
    required_resource_keys={"io_manager"},
    asset_tags={**StorageKindTagSet(storage_kind="S3")},
)


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


# This k8s pipes asset only runs in prod, see utils/example_container
# The dependency on predicted_orders is not a real dependency since the script does not rely
# or use that upstream Snowflake table, it is used here for illustrative purposes
@asset(
    deps=[predicted_orders],
    compute_kind="kubernetes",
    tags={**StorageKindTagSet(storage_kind="S3")},
)
def k8s_pod_asset(
    context: AssetExecutionContext,
    pipes_k8s_client: PipesK8sClient,
) -> MaterializeResult:
    # The kubernetes pod spec for the computation we want to run
    # with resource limits and requests set.
    pod_spec = {
        "containers": [
            {
                "name": "pipes-example",
                "image": f"{CONTAINER_REGISTRY}:latest-pipes-example",
                "resources": {
                    "requests": {
                        "memory": "64Mi",
                        "cpu": "250m",
                    },
                    "limits": {
                        "memory": "128Mi",
                        "cpu": "500m",
                    },
                },
            },
        ]
    }

    # Arbitrary json-serializable data you want access to from the `PipesSession`
    # in the k8s pod container. Assume `sample_rate` is a parameter used by
    # the target job's business logic.
    extras = {"sample_rate": 1.0}

    return pipes_k8s_client.run(
        context=context,
        namespace="data-eng-prod",
        base_pod_spec=pod_spec,
        extras=extras,
    ).get_materialize_result()