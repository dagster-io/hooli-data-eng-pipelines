from typing import Any, Tuple

import numpy as np
import pandas as pd
from scipy import optimize

import dagster as dg


from hooli_data_eng.utils.kind_helpers import get_kind
from pydantic import Field

# dynamically determine storage_kind based on environment
storage_kind = get_kind()


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


class modelHyperParams(dg.Config):
    """Hyper parameters for the ML model with default values"""

    a_init: float = Field(5, description="initial value for a parameter, intercept")
    b_init: float = Field(5, description="initial value for b parameter, slope")


@dg.asset(
    ins={"weekly_order_summary": dg.AssetIn(key_prefix=["ANALYTICS"])},
    io_manager_key="model_io_manager",
    kinds={"scikitlearn", "S3"},
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
@dg.asset(
    ins={
        "weekly_order_summary": dg.AssetIn(key_prefix=["ANALYTICS"]),
        "order_forecast_model": dg.AssetIn(),
    },
    key_prefix=["forecasting"],
    io_manager_key="model_io_manager",
    partitions_def=dg.MonthlyPartitionsDefinition(start_date="2022-01-01"),
    tags={
        "core_kpis": "",
    },
    kinds={"scikitlearn", storage_kind},
)
def model_stats_by_month(
    context,
    weekly_order_summary: pd.DataFrame,
    order_forecast_model: Tuple[float, float],
) -> dg.Output[pd.DataFrame]:
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

    return dg.Output(pd.DataFrame({"error": [error]}), metadata={"error_obs_prds": error})

