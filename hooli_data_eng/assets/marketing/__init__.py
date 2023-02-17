from dagster import asset, FreshnessPolicy, AssetIn
import pandas as pd

# These assets take data from a SQL table managed by 
# dbt and create summaries using pandas 
# The assets are updated via freshness policies 
# and an associated reconciliation sensor
@asset(
    key_prefix="MARKETING", 
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=90), 
    compute_kind="pandas",
    op_tags={"owner": "bi@hooli.com"}
)
def avg_order(company_perf: pd.DataFrame) -> pd.DataFrame:
    """ Computes avg order KPI, must be updated every 90 mins for exec dashboard """

    return pd.DataFrame({
        "avg_order": company_perf['total_revenue'] / company_perf['n_orders'] 
    })


@asset(
    key_prefix="MARKETING", 
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=90), 
    compute_kind="snowflake", 
    metadata={
        "owner": "bi@hooli.com"
    }
)
def min_order(context, company_perf: pd.DataFrame) -> pd.DataFrame:
    """ Computes min order KPI """
    min_order = min(company_perf['n_orders'])

    context.add_output_metadata({
        "min_order": min_order
    })

    return pd.DataFrame({
        "min_order": [min_order]
    })