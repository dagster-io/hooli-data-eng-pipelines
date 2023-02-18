from dagster import asset, FreshnessPolicy
import pandas as pd

# These assets take data from a SQL table managed by 
# dbt and create summaries using pandas 
# The assets are updated via freshness policies 
# and an associated reconciliation sensor
@asset(
    key_prefix="MARKETING", 
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=240), 
    compute_kind="pandas"
)
def avg_order(company_perf: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "avg_order": company_perf['total_revenue'] / company_perf['n_orders'] 
    })


@asset(
    key_prefix="MARKETING", 
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=240), 
    compute_kind="snowflake"
)
def max_order(company_perf: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "max_order": [max(company_perf['n_orders'])]
    })