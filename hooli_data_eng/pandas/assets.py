from typing import Tuple

import datetime
import numpy as np
import pandas as pd
import dagster as dg
from dagster_cloud.anomaly_detection import build_anomaly_detection_freshness_checks
from hooli_data_eng.utils.kind_helpers import get_kind


# dynamically determine storage_kind based on environment
storage_kind = get_kind()


def model_func(x, a, b):
    return a * np.exp(b * (x / 10**18 - 1.6095))


# This asset uses the trained model to forecast 30 day forward orders
# and stores the result in the warehouse
@dg.asset(
    ins={
        "weekly_order_summary": dg.AssetIn(key_prefix=["ANALYTICS"]),
        "order_forecast_model": dg.AssetIn(),
    },
    key_prefix=["FORECASTING"],
    group_name="FORECASTING",
    kinds={"pandas", storage_kind},
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


# These assets take data from a SQL table managed by
# dbt and create summaries using pandas
@dg.asset(
    key_prefix="MARKETING",
    group_name="MARKETING",
    automation_condition=dg.AutomationCondition.on_cron("0 0 1-31/2 * *"),
    owners=["team:programmers", "lopp@dagsterlabs.com"],
    ins={"company_perf": dg.AssetIn(key_prefix=["ANALYTICS"])},
    kinds={"pandas", storage_kind},
)
def avg_orders(
    context: dg.AssetExecutionContext, company_perf: pd.DataFrame
) -> pd.DataFrame:
    """Computes avg order KPI, must be updated regularly for exec dashboard"""

    return pd.DataFrame(
        {"avg_order": company_perf["total_revenue"] / company_perf["n_orders"]}
    )


@dg.asset_check(description="check that avg orders are expected", asset=avg_orders)
def check_avg_orders(context, avg_orders: pd.DataFrame):
    avg = avg_orders["avg_order"][0]
    avg_python_float = float(avg)  # Convert to Python float
    return dg.AssetCheckResult(
        passed=True if (avg_python_float < 50) else False,
        metadata={"actual average": avg_python_float, "threshold": 50},
    )


@dg.asset(
    key_prefix="MARKETING",
    group_name="MARKETING",
    owners=["team:programmers"],
    ins={"company_perf": dg.AssetIn(key_prefix=["ANALYTICS"])},
    kinds={"pandas", storage_kind},
)
def min_order(context, company_perf: pd.DataFrame) -> pd.DataFrame:
    """Computes min order KPI"""
    min_order = min(company_perf["n_orders"])

    context.add_output_metadata({"min_order": min_order})

    return pd.DataFrame({"min_order": [min_order]})


product_skus = dg.DynamicPartitionsDefinition(name="product_skus")


@dg.asset(
    partitions_def=product_skus,
    io_manager_key="model_io_manager",
    key_prefix="MARKETING",
    group_name="MARKETING",
    ins={"sku_stats": dg.AssetIn(key_prefix=["ANALYTICS"])},
    kinds={"pandas", "s3"},
)
def key_product_deepdive(context, sku_stats):
    """Creates a file for a BI tool based on the current quarters top product, represented as a dynamic partition"""
    key_sku = context.partition_key
    sku = sku_stats[sku_stats["sku"] == key_sku]
    context.add_output_metadata(
        {"sku_preview": dg.MetadataValue.md(sku.head().to_markdown())}
    )
    return sku


min_order_freshness_check = dg.build_last_update_freshness_checks(
    assets=[
        min_order,
        dg.AssetKey(["RAW_DATA", "orders"]),
        dg.AssetKey(["RAW_DATA", "users"]),
    ],
    lower_bound_delta=datetime.timedelta(
        hours=24
    ),  # expect new data at least once a day
)

avg_orders_freshness_check = build_anomaly_detection_freshness_checks(
    assets=[avg_orders], params=None
)
