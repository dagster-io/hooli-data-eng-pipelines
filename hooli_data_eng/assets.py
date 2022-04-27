import datetime
import json
import os
import random

import pandas as pd
from dagster import AssetGroup, asset
from dagster.utils import file_relative_path
from dagster_azure.adls2 import adls2_pickle_asset_io_manager, adls2_resource
from dagster_dbt import dbt_cli_resource, load_assets_from_dbt_manifest
from dagster_pyspark import pyspark_resource

from .resources.pyspark_io_manager import pyspark_parquet_asset_io_manager
from .resources.snowflake_io_manager import snowflake_io_manager
import time

DBT_PROJECT_DIR = file_relative_path(__file__, "../hacker_news_dbt")
DBT_PROFILES_DIR = file_relative_path(__file__, "../hacker_news_dbt/config")
DBT_MANIFEST_PATH = file_relative_path(__file__, "../hacker_news_dbt/target/manifest.json")


@asset(
    io_manager_key="adls2_io_manager",
    compute_kind="pandas",
)
def hacker_news_actions(context) -> pd.DataFrame:
    """User actions collected from the HackerNews API, stored in ADLS2."""
    duration = datetime.datetime.now() - datetime.datetime(2022, 3, 28)
    n_values = int(duration.total_seconds() / 360)
    columns = ["action_type", "user_id", "time"]
    data = {
        "action_type": random.choices(["comment", "story"], weights=[0.8, 0.2], k=n_values),
        "user_id": (random.randint(1000, 9999) for _ in range(n_values)),
        "time": (datetime.datetime.now().timestamp() for _ in range(n_values)),
    }
    return pd.DataFrame(data)


@asset(
    io_manager_key="adls2_io_manager",
    # required_resource_keys={"pyspark"},
    compute_kind="pandas",
    metadata={"table": "hackernews.comments"},
)
def comments(context, hacker_news_actions: pd.DataFrame):
    """Snowflake table containing HackerNews comments actions"""
    time.sleep(0.5)
    return hacker_news_actions


@asset(
    io_manager_key="adls2_io_manager",
    # required_resource_keys={"pyspark"},
    compute_kind="pandas",
    metadata={"table": "hackernews.stories"},
)
def stories(context, hacker_news_actions: pd.DataFrame):
    """Snowflake table containing HackerNews stories actions"""
    time.sleep(0.5)
    return hacker_news_actions


with open(DBT_MANIFEST_PATH, "r") as f:
    dbt_assets = load_assets_from_dbt_manifest(json.load(f))

# hack
is_remote = os.getenv("ADLS2_KEY", 1) == os.getenv("DATABRICKS_HOST", 2)

hacker_news_assets = AssetGroup(
    [hacker_news_actions, comments, stories] + dbt_assets,
    resource_defs={
        # "parquet_io_manager": pyspark_parquet_asset_io_manager.configured(
        #     {"prefix": "dbfs:/dagster"}
        # ),
        "adls2_io_manager": adls2_pickle_asset_io_manager.configured(
            {"adls2_file_system": "demofs"}
        ),
        "adls2": adls2_resource.configured(
            {"credential": {"key": os.getenv("ADLS2_KEY", "")}, "storage_account": "dagsterdemo"}
        ),
        "warehouse_io_manager": snowflake_io_manager.configured(
            {
                "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
                "user": os.getenv("SNOWFLAKE_USER", ""),
                # Hack since the snowflake password env var is being wrapped in single quotes
                "password": os.getenv("SNOWFLAKE_PASSWORD", "").strip("'"),
                "database": "TESTDB",
                "warehouse": "TINY_WAREHOUSE",
            }
        ),
        #  "pyspark": pyspark_resource,
        "dbt": dbt_cli_resource.configured(
            {
                "profiles_dir": DBT_PROFILES_DIR,
                "project_dir": DBT_PROJECT_DIR,
                "target": "assets",
            }
        ),
    },
).build_job("hacker_news_assets")
