from hooli_data_eng.assets.raw_data import orders, users, build_op_context
from hooli_data_eng.resources.api import RawDataAPI

from dagster import define_asset_job, Definitions

from dagster_duckdb_pandas import DuckDBPandasIOManager
import duckdb
import os


def test_orders_single_partition():
    orders_df = orders(
        build_op_context(
            resources={"api": RawDataAPI(flaky=False)}, partition_key="2023-04-10-22:00"
        )
    )
    assert len(orders_df) == 10


def test_users_single_partition():
    users_df = users(
        build_op_context(
            resources={"api": RawDataAPI(flaky=False)}, partition_key="2023-04-10-22:00"
        )
    )
    assert len(users_df) == 10


def test_orders_multi_partition_backfill():
    test_job = define_asset_job("test_job", selection=["orders"])
    test_resources = {
        "io_manager": DuckDBPandasIOManager(database="test.duckdb"),
        "api": RawDataAPI(flaky=False),
    }
    defs = Definitions(assets=[orders], jobs=[test_job], resources=test_resources)

    test_job_def = defs.get_job_def("test_job")
    test_job_def.execute_in_process(
        tags={
            "dagster/asset_partition_range_start": "2022-04-10-20:00",
            "dagster/asset_partition_range_end": "2022-04-10-22:00",
        },
        resources=test_resources,
    )

    con = duckdb.connect("test.duckdb")
    orders_df = con.execute("SELECT * FROM public.orders").fetchdf()
    os.remove("test.duckdb")
    assert len(orders_df) == 30


def test_users_multi_partition_backfill():
    test_job = define_asset_job("test_job", selection=["users"])
    test_resources = {
        "io_manager": DuckDBPandasIOManager(database="test.duckdb"),
        "api": RawDataAPI(flaky=False),
    }
    defs = Definitions(assets=[users], jobs=[test_job], resources=test_resources)

    test_job_def = defs.get_job_def("test_job")
    test_job_def.execute_in_process(
        tags={
            "dagster/asset_partition_range_start": "2022-04-10-20:00",
            "dagster/asset_partition_range_end": "2022-04-10-22:00",
        },
        resources=test_resources,
    )

    con = duckdb.connect("test.duckdb")
    orders_df = con.execute("SELECT * FROM public.users").fetchdf()
    os.remove("test.duckdb")
    assert len(orders_df) == 30
