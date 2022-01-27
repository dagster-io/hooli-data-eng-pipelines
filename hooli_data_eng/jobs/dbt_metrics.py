import os

from dagster import ResourceDefinition, graph
from dagster.utils import file_relative_path
from dagster_aws.s3 import s3_pickle_io_manager, s3_resource
from dagster_dbt import dbt_cli_resource

from ..ops.dbt import (
    hn_dbt_run,
    hn_dbt_test,
    preflight_comments_table,
    preflight_stories_table,
)
from ..resources.dbt_asset_resource import SnowflakeQueryDbtAssetResource

os.environ["SNOWFLAKE_PASSWORD"] = os.getenv("SNOWFLAKE_PASSWORD", "").strip("'")

DBT_PROJECT_DIR = file_relative_path(__file__, "../../hacker_news_dbt")
DBT_PROFILES_DIR = file_relative_path(__file__, "../../hacker_news_dbt/config")

SNOWFLAKE_CONF = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
    "user": os.getenv("SNOWFLAKE_USER", ""),
    "password": os.getenv("SNOWFLAKE_PASSWORD", "").strip("'"),
    "database": "DEMO_DB",
    "warehouse": "TINY_WAREHOUSE",
}

# We define two sets of resources, one for the prod job, which writes to production schemas and
# s3 buckets, and one for dev job, which writes to alternate schemas and s3 buckets.
DBT_RESOURCES_PROD = {
    "io_manager": s3_pickle_io_manager.configured(
        {"s3_bucket": "hackernews-elementl-prod"}
    ),
    "s3": s3_resource,
    "dbt": dbt_cli_resource.configured(
        {
            "profiles_dir": DBT_PROFILES_DIR,
            "project_dir": DBT_PROJECT_DIR,
            "target": "prod",
        }
    ),
    # this is an alternative pattern to the configured() api. If you know that you won't want to
    # further configure this resource per pipeline run, this can be a bit more convenient than
    # defining an @resource with a config schema.
    "dbt_assets": ResourceDefinition.hardcoded_resource(
        SnowflakeQueryDbtAssetResource(SNOWFLAKE_CONF, "hacker_news_dbt")
    ),
}


@graph
def dbt_metrics():
    comments_table_ready = preflight_comments_table()
    stories_table_ready = preflight_stories_table()
    hn_dbt_test(hn_dbt_run(comments_table_ready, stories_table_ready))


dbt_prod_job = dbt_metrics.to_job(resource_defs=DBT_RESOURCES_PROD)
