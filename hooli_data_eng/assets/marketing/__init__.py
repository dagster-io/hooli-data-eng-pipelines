from dagster import asset, FreshnessPolicy
import pandas as pd

@asset(
    key_prefix="MARKETING", 
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=90), 
    compute_kind="pandas"
)
def avg_order(company_perf: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "avg_order": company_perf['total_revenue'] / company_perf['n_orders'] 
    })


@asset(
    key_prefix="MARKETING", 
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=90), 
    compute_kind="pandas"
)
def max_order(company_perf: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "max_order": max(company_perf['n_orders'])
    })