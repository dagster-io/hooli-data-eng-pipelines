import os
from datetime import datetime

from dagster import ResourceDefinition, graph, hourly_partitioned_config
from dagster_aws.s3 import s3_pickle_io_manager, s3_resource

from ..ops.download_items import (
    build_comments,
    build_stories,
    download_items,
    update_tables,
)
from ..ops.id_range_for_time import id_range_for_time
from ..resources.hn_resource import hn_api_subsample_client
from ..resources.parquet_io_manager import partitioned_parquet_io_manager
from ..resources.snowflake_io_manager import time_partitioned_snowflake_io_manager


@hourly_partitioned_config(start_date=datetime(2021, 10, 14))
def hourly_download_schedule_config(start: datetime, end: datetime):
    return {
        "resources": {
            "partition_start": {"config": start.strftime("%Y-%m-%d %H:%M:%S")},
            "partition_end": {"config": end.strftime("%Y-%m-%d %H:%M:%S")},
        }
    }


# the configuration we'll need to make our Snowflake-based IOManager work
SNOWFLAKE_CONF = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
    "user": os.getenv("SNOWFLAKE_USER", ""),
    "password": os.getenv("SNOWFLAKE_PASSWORD", ""),
    "database": "DEMO_DB",
    "warehouse": "TINY_WAREHOUSE",
}

DOWNLOAD_RESOURCES_PROD = {
    "io_manager": s3_pickle_io_manager.configured(
        {"s3_bucket": "hackernews-elementl-prod"},
        description=(
            "Default S3 pickle IOManager that stores output values in the configured S3 bucket "
            "(`s3://hackernews-elementl-prod`)."
        ),
    ),
    "s3": s3_resource.configured({}, description="Provides access to AWS S3."),
    "partition_start": ResourceDefinition.string_resource(
        description="Specifies the start of the partition."
    ),
    "partition_end": ResourceDefinition.string_resource(
        description="Specifies the end of the partition."
    ),
    "parquet_io_manager": partitioned_parquet_io_manager.configured(
        {"base_path": "s3://hackernews-elementl-prod"},
        description=(
            "IOManager that stores partitioned DataFrames using parquet at the configured path "
            "(`s3://hackernews-elementl-prod`). Requires `partition_start` and `partition_end` "
            "resources to specify the appropriate partition."
        ),
    ),
    "warehouse_io_manager": time_partitioned_snowflake_io_manager.configured(
        SNOWFLAKE_CONF,
        description=(
            "This version of the SnowflakeIOManager divides its data into seperate time "
            "partitions. Requires partition_start and partition_end resources.\n\n"
            "Deletes the data in the Snowflake table present within those bounds, then loads "
            "output data into the table.\n\n"
            "This is useful for pipelines that run on a schedule, updating each hour (or day, "
            "etc.) with new data."
        ),
    ),
    "hn_client": hn_api_subsample_client.configured({"sample_rate": 10}),
}


DEFAULT_PARTITION_RESOURCE_CONFIG = {
    "partition_start": {"config": "2020-12-30 00:00:00"},
    "partition_end": {"config": "2020-12-30 01:00:00"},
}

DOWNLOAD_TAGS = {
    "dagster-k8s/config": {
        "container_config": {
            "resources": {
                "requests": {"cpu": "500m", "memory": "2Gi"},
            }
        },
    }
}


@graph(
    description=(
        "Ingests items from the Hacker News API, builds comments and stories dataframes, and "
        "updates the date-partitioned Snowflake tables."
    )
)
def ingest_hacker_news():
    items = download_items(id_range_for_time())
    comments_built = build_comments(items)
    stories_built = build_stories(items)
    update_tables([comments_built, stories_built])


ingest_hacker_news_job = ingest_hacker_news.to_job(
    resource_defs=DOWNLOAD_RESOURCES_PROD,
    tags=DOWNLOAD_TAGS,
    config=hourly_download_schedule_config,
    description=(
        "Date-partitioned job that ingests items from the Hacker News API, builds comments and "
        "stories dataframes, and updates the appropriate date partitions of the comments and "
        "stories tables in Snowflake."
    ),
)
