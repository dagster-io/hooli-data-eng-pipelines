from datetime import timedelta

from dagster import (
    asset,
    asset_check,
    AssetCheckSeverity,
    AssetCheckResult,
    AssetKey,
    BackfillPolicy,
    Backoff,
    DailyPartitionsDefinition,
    Jitter,
    RetryPolicy,
)
import pandas as pd


from hooli_data_eng.resources.api import RawDataAPI


daily_partitions = DailyPartitionsDefinition(
    start_date="2023-05-25"
)


def _daily_partition_seq(start, end):
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    daily_diffs = int((end - start) / timedelta(hours=24))

    return [str(start + timedelta(hours=i)) for i in range(daily_diffs)]


@asset(
    compute_kind="api",
    partitions_def=daily_partitions,
    metadata={"partition_expr": "created_at"},
    backfill_policy=BackfillPolicy.single_run()
)
def users(context, api: RawDataAPI) -> pd.DataFrame:
    """A table containing all users data"""
    # during a backfill the partition range will span multiple hours
    # during a single run the partition range will be for a single hour
    first_partition, last_partition = context.partition_time_window
    partition_seq = _daily_partition_seq(first_partition, last_partition)
    all_users = []
    for partition in partition_seq:
        resp = api.get_users(partition)
        users = pd.read_json(resp.json())
        all_users.append(users)


    return pd.concat(all_users)

@asset_check(
        asset=AssetKey(["RAW_DATA", "users"]),
        description="check that users are from expected companies",
)
def check_users(context, users: pd.DataFrame):
    unique_companies = pd.unique(users['company']).tolist()
    return AssetCheckResult(
        passed=  (unique_companies == ["FoodCo", "ShopMart", "SportTime", "FamilyLtd"]),
        metadata={"companies": unique_companies},
        severity=AssetCheckSeverity.WARN
    )

@asset(
    compute_kind="api",
    partitions_def=daily_partitions,
    metadata={"partition_expr": "DT"},
    retry_policy=RetryPolicy(
        max_retries=3,
        delay=1,
        backoff=Backoff.LINEAR,
        jitter=Jitter.FULL
    ),
    backfill_policy=BackfillPolicy.single_run()
)
def orders(context, api: RawDataAPI) -> pd.DataFrame:
    """A table containing all orders that have been placed"""
    first_partition, last_partition = context.partition_time_window
    partition_seq = _daily_partition_seq(first_partition, last_partition)
    all_orders = []
    for partition in partition_seq:
        resp = api.get_orders(partition)
        users = pd.read_json(resp.json())
        all_orders.append(users)

    all_orders_df = pd.concat(all_orders)
    all_orders_df['dt'] = pd.to_datetime(all_orders_df['dt'], unit = "ms")
    return all_orders_df


from dagster_dbt import dbt_assets
