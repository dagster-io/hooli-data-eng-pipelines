from dagster import asset, FreshnessPolicy, AssetIn, DynamicPartitionsDefinition, MetadataValue, AutoMaterializePolicy
import pandas as pd

# These assets take data from a SQL table managed by 
# dbt and create summaries using pandas 
# The assets are updated via freshness policies 
# and an associated reconciliation sensor
@asset(
    key_prefix="MARKETING", 
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=240), 
    auto_materialize_policy=AutoMaterializePolicy.lazy(),
    compute_kind="pandas",
    op_tags={"owner": "bi@hooli.com"}
)
def avg_order(company_perf: pd.DataFrame) -> pd.DataFrame:
    """ Computes avg order KPI, must be updated regularly for exec dashboard """

    return pd.DataFrame({
        "avg_order": company_perf['total_revenue'] / company_perf['n_orders'] 
    })


@asset(
    key_prefix="MARKETING", 
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=240), 
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


product_skus = DynamicPartitionsDefinition(name="product_skus")

@asset(
    partitions_def=product_skus,
    io_manager_key="model_io_manager",
    compute_kind="hex",
    key_prefix="MARKETING",
    ins={"sku_stats": AssetIn(key_prefix=["ANALYTICS"])}
)
def key_product_deepdive(context, sku_stats):
    """ Creates a file for a BI tool based on the current quarters top product, represented as a dynamic partition """
    key_sku = context.partition_key
    sku = sku_stats[sku_stats['sku'] == key_sku]
    context.add_output_metadata(
        {
            "sku_preview": MetadataValue.md(sku.head().to_markdown())
        }
    )
    return sku