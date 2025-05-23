from pathlib import Path
import os
from databricks.sdk import WorkspaceClient
from unittest import mock
import dagster as dg
from dagster_databricks import PipesDatabricksClient, databricks_pyspark_step_launcher
from hooli_data_eng.utils import get_env
from dagster_databricks import databricks_client


# Configure the Databricks client resource
databricks_client_instance = databricks_client.configured(
    {
        "host": {"env": "DATABRICKS_HOST"},
        "token": {"env": "DATABRICKS_TOKEN"},
    }
)


def launch_and_poll_databricks_job(context, client, job_id):
    jobs_service = client.workspace_client.jobs

    run = jobs_service.run_now(
        job_id=job_id,
    )
    run_id = run.bind()["run_id"]

    get_run_response = jobs_service.get_run(run_id=run_id)

    context.log.info(
        f"Launched databricks job run for '{get_run_response.run_name}' (`{run_id}`). URL:"
        f" {get_run_response.run_page_url}. Waiting to run to complete."
    )

    client.wait_for_run_to_complete(
        logger=context.log,
        databricks_run_id=run_id,
        poll_interval_sec=5,
        max_wait_time_sec=600,
    )


# The production deployment on Dagster Cloud uses production Snowflake
# and S3 resources
client = mock.MagicMock()

if get_env() == "PROD":
    # Databricks Client
    client = WorkspaceClient(
        host=os.environ["DATABRICKS_HOST"],
        token=os.environ["DATABRICKS_TOKEN"],
    )

# ---------------------------------------------------
# This resource allows the big_orders asset to
# run on a databricks cluster in branch or prod
# (Locally the asset uses a local pyspark session)

# During asset evaluation, a new cluster is created
# and the project code is sent to the cluster using a
# *step launcher*
# Existing clusters can be used instead of creating a
# job-specific cluster by changing the cluster key to
# "cluster": {"existing": "cluster-id"}

cluster_config = {
    "size": {"num_workers": 1},
    "spark_version": "11.2.x-scala2.12",
    "nodes": {"node_types": {"node_type_id": "i3.xlarge"}},
}

db_step_launcher = databricks_pyspark_step_launcher.configured(
    {
        "run_config": {
            "run_name": "launch_step",
            "cluster": {"new": cluster_config},
            "libraries": [
                {"pypi": {"package": "dagster-aws"}},
                {"pypi": {"package": "dagster-pandas"}},
                {"pypi": {"package": "dagster-dbt"}},
                {"pypi": {"package": "dagster-duckdb"}},
                {"pypi": {"package": "dagster-duckdb-pandas"}},
                {"pypi": {"package": "dbt-core"}},
                {"pypi": {"package": "dbt-duckdb"}},
                {"pypi": {"package": "dbt-snowflake"}},
                {"pypi": {"package": "dagster-cloud"}},
                {"pypi": {"package": "pandas>=1.4.0"}},
                {"pypi": {"package": "dagster-snowflake"}},
                {"pypi": {"package": "dagster-snowflake-pandas"}},
                {"pypi": {"package": "dagster-pyspark"}},
                {"pypi": {"package": "requests"}},
                {"pypi": {"package": "numpy"}},
                {"pypi": {"package": "scipy"}},
                {"pypi": {"package": "plotnine"}},
                {"pypi": {"package": "dagstermill"}},
                {"pypi": {"package": "responses"}},
                {"pypi": {"package": "requests"}},
            ],
        },
        "databricks_host": {"env": "DATABRICKS_HOST"},
        "databricks_token": {"env": "DATABRICKS_TOKEN"},
        "local_pipeline_package_path": str(Path(__file__).parent.parent.parent),
        "env_variables": {
            "DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT": os.getenv(
                "DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", ""
            ),
            "DAGSTER_CLOUD_DEPLOYMENT_NAME": os.getenv(
                "DAGSTER_CLOUD_DEPLOYMENT_NAME", ""
            ),
        },
        "secrets_to_env_variables": [
            {"name": "DATABRICKS_HOST", "key": "adls2_key", "scope": "dagster-test"},
            {"name": "DATABRICKS_TOKEN", "key": "adls2_key", "scope": "dagster-test"},
            {
                "name": "SNOWFLAKE_USER",
                "key": "snowflake_user",
                "scope": "dagster-test",
            },
            {
                "name": "SNOWFLAKE_PASSWORD",
                "key": "snowflake_password",
                "scope": "dagster-test",
            },
            {
                "name": "SNOWFLAKE_ACCOUNT",
                "key": "snowflake_account",
                "scope": "dagster-test",
            },
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


resource_def = {
    "LOCAL": {
        "step_launcher": dg.ResourceDefinition.none_resource(),
        "pipes_databricks_client": dg.ResourceDefinition.none_resource(),
        "databricks": databricks_client_instance,
    },
    "BRANCH": {
        "step_launcher": db_step_launcher,
        "pipes_databricks_client": dg.ResourceDefinition.none_resource(),
        "databricks": databricks_client_instance,
    },
    "PROD": {
        "step_launcher": db_step_launcher,
        "pipes_databricks_client": PipesDatabricksClient(client),
        "databricks": databricks_client_instance,
    },
}
