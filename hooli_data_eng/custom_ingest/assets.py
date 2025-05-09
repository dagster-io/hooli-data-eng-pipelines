from datetime import timedelta
import dagster as dg
import pandas as pd

from hooli_data_eng.custom_ingest.resources import RawDataAPI
from hooli_data_eng.utils.kind_helpers import get_kind


# dynamically determine storage_kind based on environment
storage_kind = get_kind()


daily_partitions = dg.DailyPartitionsDefinition(start_date="2023-05-25")


def _daily_partition_seq(start, end):
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    daily_diffs = int((end - start) / timedelta(hours=24))

    return [str(start + timedelta(hours=i)) for i in range(daily_diffs)]


@dg.asset(
    partitions_def=daily_partitions,
    metadata={"partition_expr": "created_at"},
    backfill_policy=dg.BackfillPolicy.single_run(),
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


@dg.asset_check(
    asset=dg.AssetKey(["RAW_DATA", "users"]),
    description="check that users are from expected companies",
)
def check_users(context, users: pd.DataFrame):
    observed_companies = set(pd.unique(users["company"]))
    expected_companies = {"ShopMart", "SportTime", "FamilyLtd", "DiscountStore"}

    return dg.AssetCheckResult(
        passed=(set(observed_companies) == expected_companies),
        metadata={
            "result": dg.MetadataValue.md(
                f"""
                Observed the following unexpected companies: 
                {list(observed_companies - expected_companies)}
            """
            )
        },
        severity=dg.AssetCheckSeverity.WARN,
    )


@dg.asset(
    partitions_def=daily_partitions,
    metadata={"partition_expr": "DT"},
    retry_policy=dg.RetryPolicy(
        max_retries=3, delay=1, backoff=dg.Backoff.LINEAR, jitter=dg.Jitter.FULL
    ),
    backfill_policy=dg.BackfillPolicy.single_run(),
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
    all_orders_df["dt"] = pd.to_datetime(all_orders_df["dt"], unit="ms")
    return all_orders_df


raw_data_schema_checks = dg.build_column_schema_change_checks(
    assets=[
        dg.AssetKey(["RAW_DATA", "orders"]),
        dg.AssetKey(["RAW_DATA", "users"]),
    ]
)
