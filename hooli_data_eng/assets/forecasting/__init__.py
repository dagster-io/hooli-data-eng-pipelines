from typing import Any, Tuple

import numpy as np
import pandas as pd
from scipy import optimize
from dagster_dbt import DbtCliResource

from dagster import AssetIn, asset,  MonthlyPartitionsDefinition, Output, Field, Int
from dagstermill import define_dagstermill_asset
from dagster._utils import file_relative_path

def model_func(x, a, b):
    return a * np.exp(b * (x / 10**18 - 1.6095))

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
@asset(
    ins={"daily_order_summary": AssetIn(key_prefix=["ANALYTICS"])},
    compute_kind="ml_tool",
    io_manager_key="model_io_manager",
    config_schema={"a_init": Field(Int, default_value=5), "b_init": Field(Int, default_value=5)}
    
)
def order_forecast_model(context, daily_order_summary: pd.DataFrame) -> Any:


    """Model parameters that best fit the observed data"""
    df = daily_order_summary
    p0 = [context.op_config["a_init"], context.op_config["b_init"]]
    coeffs = tuple(
        optimize.curve_fit(
            f=model_func, xdata=df.order_date.astype(np.int64), ydata=df.num_orders, p0=p0
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
        "daily_order_summary": AssetIn(key_prefix=["ANALYTICS"]),
        "order_forecast_model": AssetIn(),
    },
    compute_kind="ml_tool",
    key_prefix=["forecasting"],
    io_manager_key="model_io_manager",
    partitions_def=MonthlyPartitionsDefinition(start_date="2022-01-01")
)
def model_stats_by_month(context, daily_order_summary: pd.DataFrame, order_forecast_model: Tuple[float, float]) -> Output[pd.DataFrame]:
    """Model errors by month"""
    a, b = order_forecast_model
    target_date = pd.to_datetime(context.asset_partition_key_for_output())
    target_month = target_date.month
    daily_order_summary['order_date'] = pd.to_datetime(daily_order_summary['order_date'])
    daily_order_summary['order_month'] = pd.DatetimeIndex(daily_order_summary['order_date']).month
    target_orders = daily_order_summary[(daily_order_summary['order_month'] == target_month)]
    date_range  = pd.date_range(
        start=target_date, end=target_date + pd.DateOffset(days=30)
    )
    predicted_orders = model_func(x = date_range.astype(np.int64), a=a, b=b)
    error = sum(target_orders['num_orders']) - sum(predicted_orders)
    context.log.info("Error for " + str(target_date) + ": " + str(error))
    
    return Output(pd.DataFrame({"error": [error]}), metadata={"error_obs_prds": error})


# This asset uses the trained model to forecast 30 day forward orders
# and stores the result in the warehouse
@asset(
    ins={
        "daily_order_summary": AssetIn(key_prefix=["ANALYTICS"]),
        "order_forecast_model": AssetIn(),
    },
    compute_kind="ml_tool",
    key_prefix=["FORECASTING"],
)
def predicted_orders(
    daily_order_summary: pd.DataFrame, order_forecast_model: Tuple[float, float]
) -> pd.DataFrame:
    """Predicted orders for the next 30 days based on the fit paramters"""
    a, b = order_forecast_model
    start_date = daily_order_summary.order_date.max()
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
    metadata = {"resource_constrained_at": 50}
)
def big_orders(context,predicted_orders: pd.DataFrame):
    """Days where predicted orders surpass our current carrying capacity"""
    df = context.resources.pyspark.spark_session.createDataFrame(predicted_orders)
    return df.where(df.num_orders >= 50).toPandas()

# This asset uses a Jupyter Notebook which takes inputs from the warehouse
# and the trained model coefficients
model_nb = define_dagstermill_asset(
    name = "model_nb",
    notebook_path = file_relative_path(__file__, "model.ipynb"),
    ins = {
          "daily_order_summary": AssetIn(key_prefix=["ANALYTICS"], dagster_type = pd.DataFrame),
          "order_forecast_model": AssetIn(),
    },
    required_resource_keys = {"io_manager"}
) 