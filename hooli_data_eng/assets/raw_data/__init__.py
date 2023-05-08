import pandas as pd
from dagster import asset, RetryPolicy, Backoff, Jitter, HourlyPartitionsDefinition, OpExecutionContext, build_op_context, build_resources
from datetime import datetime, timedelta
from hooli_data_eng.resources.api import RawDataAPI


hourly_partitions = HourlyPartitionsDefinition(
    start_date="2023-04-11-00:00"
)


def _hourly_partition_seq(start, end):
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    hourly_diffs = int((end - start) / timedelta(hours=1))
    
    return [str(start + timedelta(hours=i)) for i in range(hourly_diffs)]


@asset(
    compute_kind="api",
    partitions_def=hourly_partitions,
    metadata={"partition_expr": "created_at"},
)
def users(context, api: RawDataAPI) -> pd.DataFrame:
    """A table containing all users data"""
    # during a backfill the partition range will span multiple hours
    # during a single run the partition range will be for a single hour
    first_partition, last_partition = context.asset_partitions_time_window_for_output()
    partition_seq = _hourly_partition_seq(first_partition, last_partition)
    all_users = []
    for partition in partition_seq:
        resp = api.get_users(partition)
        users = pd.read_json(resp.json())
        all_users.append(users)

    return pd.concat(all_users)


@asset(
    compute_kind="api",
    partitions_def=hourly_partitions,
    metadata={"partition_expr": "DT"},
    retry_policy=RetryPolicy(
        max_retries=3, 
        delay=1, 
        backoff=Backoff.LINEAR,
        jitter=Jitter.FULL
    ),
)
def orders(context, api: RawDataAPI) -> pd.DataFrame:
    """A table containing all orders that have been placed"""
    first_partition, last_partition = context.asset_partitions_time_window_for_output()
    partition_seq = _hourly_partition_seq(first_partition, last_partition)
    all_orders = []
    for partition in partition_seq:
        resp = api.get_orders(partition)
        users = pd.read_json(resp.json())
        all_orders.append(users)
    
    all_orders_df = pd.concat(all_orders)
    all_orders_df['dt'] = pd.to_datetime(all_orders_df['dt'], unit = "ms")
    return all_orders_df