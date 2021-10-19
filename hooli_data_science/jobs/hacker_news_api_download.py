import os

from dagster import ResourceDefinition, graph
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
from ..schedules.hourly_hn_download_schedule import hourly_download_schedule_config

# the configuration we'll need to make our Snowflake-based IOManager work
SNOWFLAKE_CONF = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
    "user": os.getenv("SNOWFLAKE_USER", ""),
    "password": os.getenv("SNOWFLAKE_PASSWORD", ""),
    "database": "DEMO_DB",
    "warehouse": "TINY_WAREHOUSE",
}

DOWNLOAD_RESOURCES_STAGING = {
    "io_manager": s3_pickle_io_manager.configured(
        {"s3_bucket": "hackernews-elementl-dev"}
    ),
    "s3": s3_resource,
    "partition_start": ResourceDefinition.string_resource(),
    "partition_end": ResourceDefinition.string_resource(),
    "parquet_io_manager": partitioned_parquet_io_manager.configured(
        {"base_path": "s3://hackernews-elementl-dev"}
    ),
    "warehouse_io_manager": time_partitioned_snowflake_io_manager.configured(
        SNOWFLAKE_CONF
    ),
    "hn_client": hn_api_subsample_client.configured({"sample_rate": 10}),
    "base_url": ResourceDefinition.hardcoded_resource(
        "http://demo.elementl.dev", "Dagit URL"
    ),
}

DOWNLOAD_RESOURCES_PROD = {
    "io_manager": s3_pickle_io_manager.configured(
        {"s3_bucket": "hackernews-elementl-prod"}
    ),
    "s3": s3_resource,
    "partition_start": ResourceDefinition.string_resource(),
    "partition_end": ResourceDefinition.string_resource(),
    "parquet_io_manager": partitioned_parquet_io_manager.configured(
        {"base_path": "s3://hackernews-elementl-prod"}
    ),
    "warehouse_io_manager": time_partitioned_snowflake_io_manager.configured(
        SNOWFLAKE_CONF
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

# FIXME: Need to change the owners
@graph(
    description="#### Owners:\n"
    "schrockn@elementl.com, cat@elementl.com\n "
    "#### About\n"
    "This pipeline downloads all items from the HN API for a given day, "
    "splits the items into stories and comment types using Spark, and uploads filtered items to "
    "the corresponding stories or comments Snowflake table",
)
def hacker_news_api_download():
    items = download_items(id_range_for_time())
    _, comments_built = build_comments(items)
    _, stories_built = build_stories(items)
    update_tables([comments_built, stories_built])


download_prod_job = hacker_news_api_download.to_job(
    resource_defs=DOWNLOAD_RESOURCES_PROD,
    tags=DOWNLOAD_TAGS,
    config=hourly_download_schedule_config,
)


download_staging_job = hacker_news_api_download.to_job(
    resource_defs=DOWNLOAD_RESOURCES_STAGING,
    tags=DOWNLOAD_TAGS,
    config=hourly_download_schedule_config,
)
