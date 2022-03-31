import json
from pathlib import Path
import os
import random
import pyspark
import datetime
from dagster.utils import file_relative_path

from dagster import asset, AssetGroup, ResourceDefinition
from dagster_databricks import databricks_pyspark_step_launcher
from dagster_pyspark import pyspark_resource
from dagster_azure.adls2 import adls2_resource
from dagster_dbt import dbt_cli_resource, load_assets_from_dbt_manifest
from .resources.pyspark_io_manager import pyspark_parquet_asset_io_manager

DBT_PROJECT_DIR = file_relative_path(__file__, "../hacker_news_dbt")
DBT_PROFILES_DIR = file_relative_path(__file__, "../hacker_news_dbt/config")
DBT_MANIFEST_PATH = file_relative_path(__file__, "../hacker_news_dbt/target/manifest.json")

db_step_launcher = databricks_pyspark_step_launcher.configured(
    {
        "run_config": {
            "run_name": "launch_step",
            "cluster": {"existing": "0330-205159-1zaw1cv6"},
            "libraries": [
                {"pypi": {"package": "dagster-azure"}},
                {"pypi": {"package": "dagster-aws"}},
                {"pypi": {"package": "dagster-pandas"}},
                {"pypi": {"package": "dagster-dbt"}},
                {"pypi": {"package": "dbt-core"}},
                {"pypi": {"package": "dbt-snowflake"}},
                {"pypi": {"package": "dagster-fivetran"}},
                {"pypi": {"package": "dagster-cloud"}},
                {"pypi": {"package": "snowflake-sqlalchemy"}},
                {"pypi": {"package": "requests"}},
            ],
        },
        "databricks_host": {"env": "DATABRICKS_HOST"},
        "databricks_token": {"env": "DATABRICKS_TOKEN"},
        "local_pipeline_package_path": str(Path(__file__).parent.parent),
        "secrets_to_env_variables": [
            {"name": "ADLS2_KEY", "key": "adls2_key", "scope": "dagster-test"},
            {"name": "DATABRICKS_HOST", "key": "adls2_key", "scope": "dagster-test"},
            {"name": "DATABRICKS_TOKEN", "key": "adls2_key", "scope": "dagster-test"},
        ],
        "storage": {
            "s3": {
                "access_key_key": "access_key_key",
                "secret_key_key": "secret_key_key",
                "secret_scope": "dagster-test",
            }
        },
    }
)


@asset(
    io_manager_key="pyspark_io_manager",
    compute_kind="databricks",
    required_resource_keys={"step_launcher", "pyspark"},
)
def source_dataset(context):
    """ """
    duration = datetime.datetime.now() - datetime.datetime(2022, 3, 28)
    n_values = int(duration.total_seconds() / 360)
    columns = ["action_type", "user_id"]
    data = zip(
        random.choices(["comment", "story"], weights=[0.8, 0.2], k=n_values),
        (random.randint(1000, 9999) for _ in range(n_values)),
    )

    return context.resources.pyspark.spark_session.createDataFrame(data, columns)


@asset(
    io_manager_key="pyspark_io_manager",
    required_resource_keys={"step_launcher"},
    compute_kind="databricks",
)
def comments(source_dataset):
    return source_dataset.where(source_dataset.action_type == "comment")


@asset(
    io_manager_key="pyspark_io_manager",
    required_resource_keys={"step_launcher"},
    compute_kind="databricks",
)
def stories(source_dataset):
    return source_dataset.where(source_dataset.action_type == "story")


with open(DBT_MANIFEST_PATH, "r") as f:
    dbt_assets = load_assets_from_dbt_manifest(json.load(f))


ag = AssetGroup(
    [source_dataset, comments, stories] + dbt_assets,
    resource_defs={
        "pyspark_io_manager": pyspark_parquet_asset_io_manager.configured(
            {"prefix": "dbfs:/dagster"}
        ),
        "pyspark": pyspark_resource,
        # "step_launcher": ResourceDefinition.mock_resource(),
        "step_launcher": db_step_launcher,
        "dbt": dbt_cli_resource.configured(
            {
                "profiles_dir": DBT_PROFILES_DIR,
                "project_dir": DBT_PROJECT_DIR,
                "target": "prod",
            }
        ),
    },
).build_job("assets")
