from typing import Any, Tuple

import numpy as np
import pandas as pd
from scipy import optimize

from dagster import AssetIn, asset


def model_func(x, a, b):
    return a * np.exp(b * (x / 10**18 - 1.6095))


@asset(
    ins={"daily_order_summary": AssetIn(key_prefix=["analytics"])},
    compute_kind="ml_tool",
    io_manager_key="model_io_manager",
    config_schema={"a_init": int, "b_init": int}
    
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

@asset(
    ins={
        "daily_order_summary": AssetIn(key_prefix=["analytics"]),
        "order_forecast_model": AssetIn(),
    },
    compute_kind="ml_tool",
    key_prefix=["forecasting"],
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
