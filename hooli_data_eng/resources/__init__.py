import os

from dagster import EnvVar, FilesystemIOManager, ResourceDefinition
from dagster._utils import file_relative_path
from dagster_aws.s3 import ConfigurablePickledObjectS3IOManager, S3Resource
from dagster_dbt import DbtCliResource
from dagster_duckdb_pandas import DuckDBPandasIOManager
from dagster_k8s import PipesK8sClient
from dagster_pyspark import pyspark_resource
from dagster_snowflake_pandas import SnowflakePandasIOManager
from dagstermill import ConfigurableLocalOutputNotebookIOManager

from hooli_data_eng.project import (
    dbt_project,
    get_env,
    DBT_PROJECT_DIR,
)
from hooli_data_eng.resources.api import RawDataAPI
from hooli_data_eng.resources.databricks import db_step_launcher

# from hooli_data_eng.resources.dbt import DbtCli2 as DbtCli
# from hooli_data_eng.resources.warehouse import MySnowflakeIOManager as SnowflakePandasIOManager
from hooli_data_eng.resources.sensor_file_managers import s3FileSystem, LocalFileSystem

from databricks.sdk import WorkspaceClient
from dagster_databricks import PipesDatabricksClient
from unittest import mock

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
# The production deployment on Dagster Cloud uses production Snowflake
# and S3 resources
client = mock.MagicMock()

if get_env() in ["PROD", "LOCAL"]:
    # Databricks Client
    client = WorkspaceClient(
        host=os.environ["DATABRICKS_HOST"],
        token=os.environ["DATABRICKS_TOKEN"],
    )

# The dbt file dbt_project/config/profiles.yaml
# specifies what databases to targets, and locally will
# execute against a DuckDB

# Similar to having different dbt targets, here we create the resource
# configuration by environment

resource_def = {
    "LOCAL": {
        "io_manager": DuckDBPandasIOManager(
            database=os.path.join(DBT_PROJECT_DIR, "example.duckdb")
        ),
        "model_io_manager": FilesystemIOManager(),
        "output_notebook_io_manager": ConfigurableLocalOutputNotebookIOManager(),
        "api": RawDataAPI.configure_at_launch(),
        "s3": ResourceDefinition.none_resource(),
        "dbt": DbtCliResource(project_dir=dbt_project, target="LOCAL"),
        "dbt2": DbtCliResource(project_dir=dbt_project, target="LOCAL"),
        "pyspark": pyspark_resource,
        "step_launcher": ResourceDefinition.none_resource(),
        "monitor_fs": LocalFileSystem(base_dir=file_relative_path(__file__, ".")),
        "email": LocalEmailAlert(
            smtp_email_to=["data@awesome.com"], smtp_email_from="no-reply@awesome.com"
        ),
        "pipes_databricks_client": PipesDatabricksClient(client),
        "pipes_k8s_client": ResourceDefinition.none_resource(),
    },
    "BRANCH": {
        "io_manager": SnowflakePandasIOManager(
            database="DEMO_DB2_BRANCH",
            account=EnvVar("SNOWFLAKE_ACCOUNT"),
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
            warehouse="TINY_WAREHOUSE",
        ),
        "model_io_manager": ConfigurablePickledObjectS3IOManager(
            s3_bucket="hooli-demo-branch",
            s3_resource=S3Resource(region_name="us-west-2"),
        ),
        "output_notebook_io_manager": ConfigurableLocalOutputNotebookIOManager(),
        "api": RawDataAPI.configure_at_launch(),
        "dbt": DbtCliResource(project_dir=dbt_project, target="BRANCH"),
        "dbt2": DbtCliResource(project_dir=dbt_project, target="BRANCH"),
        "pyspark": pyspark_resource,
        "step_launcher": db_step_launcher,
        "monitor_fs": s3FileSystem(
            region_name="us-west-2", s3_bucket="hooli-demo-branch"
        ),
        "pipes_databricks_client": ResourceDefinition.none_resource(),
        "pipes_k8s_client": PipesK8sClient(),
    },
    "PROD": {
        "io_manager": SnowflakePandasIOManager(
            database="DEMO_DB2",
            account=EnvVar("SNOWFLAKE_ACCOUNT"),
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
            warehouse="TINY_WAREHOUSE",
        ),
        "model_io_manager": ConfigurablePickledObjectS3IOManager(
            s3_bucket="hooli-demo-branch",
            s3_resource=S3Resource(region_name="us-west-2"),
        ),
        "output_notebook_io_manager": ConfigurableLocalOutputNotebookIOManager(),
        "api": RawDataAPI.configure_at_launch(),
        "dbt": DbtCliResource(project_dir=dbt_project, target="PROD"),
        "dbt2": DbtCliResource(project_dir=dbt_project, target="PROD"),
        "pyspark": pyspark_resource,
        "step_launcher": db_step_launcher,
        "monitor_fs": s3FileSystem(region_name="us-west-2", s3_bucket="hooli-demo"),
        "pipes_databricks_client": PipesDatabricksClient(client),
        "pipes_k8s_client": PipesK8sClient(),
    },
}
