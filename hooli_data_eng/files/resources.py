from dagster._utils import file_relative_path
from hooli_data_eng.files.sensor_file_managers import s3FileSystem, LocalFileSystem

# Resources represent external systems and, and specifically IO Managers
# tell dagster where our assets should be materialized. In dagster
# resources are separate from logical code to make it possible
# to develop locally, run tests, and run integration tests
#
# This project is designed for everything to run locally
# using the file system and DuckDB as the primary development resources
#
# PRs use a "branch" environment that mirrors production with
# staging Snowflake and S3 resources
#


resource_def = {
    "LOCAL": {
        "monitor_fs": LocalFileSystem(base_dir=file_relative_path(__file__, ".")),
    },
    "BRANCH": {
        "monitor_fs": s3FileSystem(
            region_name="us-west-2", s3_bucket="hooli-demo-branch"
        ),
    },
    "PROD": {
        "monitor_fs": s3FileSystem(region_name="us-west-2", s3_bucket="hooli-demo"),
    },
}
