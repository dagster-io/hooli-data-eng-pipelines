from datetime import timedelta

from dagster import (
    asset,
    asset_check,
    AssetCheckSeverity,
    AssetCheckResult,
    AssetKey,
    BackfillPolicy,
    Backoff,
    build_column_schema_change_checks,
    Backoff,
    DailyPartitionsDefinition,
    Jitter,
    MetadataValue,
    RetryPolicy,
)
from dagster._core.definitions.tags import build_kind_tag
import pandas as pd

from hooli_data_eng.resources.api import RawDataAPI
from hooli_data_eng.utils.kind_helpers import get_storage_kind


# dynamically determine storage_kind based on environment
storage_kind = get_kind()


daily_partitions = DailyPartitionsDefinition(
    start_date="2023-05-25"
)


def _daily_partition_seq(start, end):
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    daily_diffs = int((end - start) / timedelta(hours=24))
    
    return [str(start + timedelta(hours=i)) for i in range(daily_diffs)]


@asset(
    partitions_def=daily_partitions,
    metadata={"partition_expr": "created_at"},
    backfill_policy=BackfillPolicy.single_run(),
    kinds={"api", storage_kind},
)
def users(context, api: RawDataAPI) -> pd.DataFrame:
    """A table containing all users data"""
    # during a backfill the partition range will span multiple hours
    # during a single run the partition range will be for a single hour
    first_partition, last_partition = context.asset_partitions_time_window_for_output()
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
    observed_companies = set(pd.unique(users['company']))
    expected_companies = {"ShopMart", "SportTime", "FamilyLtd", "DiscountStore"}

    return AssetCheckResult(
        passed=  (set(observed_companies) == expected_companies),
        metadata={"result": MetadataValue.md(
            f"""
                Observed the following unexpected companies: 
                {list(observed_companies - expected_companies)}
            """
        )},
        severity=AssetCheckSeverity.WARN
    )

@asset(
    partitions_def=daily_partitions,
    metadata={"partition_expr": "DT"},
    retry_policy=RetryPolicy(
        max_retries=3, 
        delay=1, 
        backoff=Backoff.LINEAR,
        jitter=Jitter.FULL
    ),
    backfill_policy=BackfillPolicy.single_run(),
    kinds={"api", storage_kind},
)
def orders(context, api: RawDataAPI) -> pd.DataFrame:
    """A table containing all orders that have been placed"""
    first_partition, last_partition = context.asset_partitions_time_window_for_output()
    partition_seq = _daily_partition_seq(first_partition, last_partition)
    all_orders = []
    for partition in partition_seq:
        resp = api.get_orders(partition)
        users = pd.read_json(resp.json())
        all_orders.append(users)
    
    all_orders_df = pd.concat(all_orders)
    all_orders_df['dt'] = pd.to_datetime(all_orders_df['dt'], unit = "ms")
    return all_orders_df

raw_data_schema_checks = build_column_schema_change_checks(assets=[
    AssetKey(["RAW_DATA", "orders"]),
    AssetKey(["RAW_DATA", "users"]),
])
