import json

from dagster import (
    asset,
    OpExecutionContext,
    MetadataValue,
    DynamicOut,
    op,
    DynamicOutput,
    graph_asset,
    RetryPolicy,
    Config,
)
import pandas as pd
from pydantic import Field
import numpy as np

from dagster_batch_enrichment.warehouse import MyWarehouse
from dagster_batch_enrichment.api import EnrichmentAPI


class experimentConfig(Config):
    experiment_name: str = Field(
        default="default_config",
        description="A name to give to this run's configuration set",
    )


@asset(
    kinds={"Kubernetes", "S3"},
)
def raw_data(
    context: OpExecutionContext,
    warehouse: MyWarehouse,
    config: experimentConfig,
):
    """Placeholder for querying a real data source"""
    orders_to_process = warehouse.get_raw_data()

    # add any logging
    context.log.info(f"Received {len(orders_to_process)} orders to process")

    # associate metadata with the raw data asset materialization
    context.add_output_metadata(
        metadata={
            "preview": MetadataValue.md(orders_to_process.head(3).to_markdown()),
            "nrows": len(orders_to_process),
            "user_input": config.experiment_name,
        }
    )

    return orders_to_process


# The enriched_data asset is constructed from a graph of operations
# that splits the raw data into batches and calls an enrichment API
# for each batch
# The batch size is configurable with a default of 50 records per batch
# The batches are processed in parallel threads
class ParallelizationConfig(Config):
    number_records_per_batch: int = Field(
        50, description="Number of records to use per batch"
    )


@op(out=DynamicOut())
def split_rows(context: OpExecutionContext, raw_data, config: ParallelizationConfig):
    """
    Split a data frame into batches
    """
    n_chunks = np.ceil(len(raw_data) / config.number_records_per_batch)
    chunks = np.array_split(raw_data, n_chunks)
    r = 0
    for c in chunks:
        r = r + 1
        yield DynamicOutput(c, mapping_key=str(r))


@op(retry_policy=RetryPolicy(max_retries=2))
def process_chunk(
    context: OpExecutionContext, chunk, api: EnrichmentAPI
) -> pd.DataFrame:
    """
    Process rows in each chunk by calling the enrichment API
        within a chunk processing is sequential
        but it could be parallelized with regular python techniques
    """
    chunk["order_center"] = chunk.apply(
        lambda row: get_order_details(row["order_id"], api), axis=1
    )
    return chunk


def get_order_details(order_id, api):
    """Given an order id call the enrichment API to get an order center"""
    response = api.get_order_details(order_id)
    response_data = json.loads(response.json())
    return response_data["order_center"]


@op
def concat_chunk_list(chunks) -> pd.DataFrame:
    """Merge the processed chunks back together"""
    return pd.concat(chunks)


@graph_asset(
    kinds={"Kubernetes", "S3"},
)
def enriched_data(raw_data) -> pd.DataFrame:
    """Full enrichment process"""
    chunks = split_rows(raw_data)
    chunks_mapped = chunks.map(process_chunk)
    enriched_chunks = chunks_mapped.collect()
    return concat_chunk_list(enriched_chunks)
