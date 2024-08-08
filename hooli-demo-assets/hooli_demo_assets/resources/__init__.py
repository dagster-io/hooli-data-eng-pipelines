import os
from pathlib import Path

from dagster import EnvVar
from dagster_embedded_elt.sling import (
   SlingResource,
   SlingConnectionResource,
)


def get_env():
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "data-eng-prod":
        return "PROD"
    if os.getenv("DAGSTER_IS_DEV_CLI"):
        return "LOCAL"
    # default to BRANCH so we use that in github CI
    return "BRANCH"


# Path for duckdb connection - needed for local dev
current_file_path = Path(__file__)
parent_dir_path = current_file_path.parent.parent.parent.parent
DUCKDB_PATH = parent_dir_path / "dbt_project" / "example.duckdb"


# Alternatively a replication.yaml file can be used
def create_replication_config(env: str):
   # Determine the target database dynamically based on the environment
   target_database = {
       'LOCAL': 'DUCKDB',
       'BRANCH': 'SNOWFLAKE_BRANCH',
       'PROD': 'SNOWFLAKE_PROD'
   }.get(env, 'DUCKDB')  # Default to DUCKDB if no environment matches

   replication_config = {
       "source": "S3",
       "target": target_database,
       "defaults": {
           "mode": "full-refresh",
           "object": "{stream_file_folder}.{stream_file_name}",
           "source_options": {
               "format": "csv"
           }
       },
       "streams": {
           "s3://hooli-demo/embedded-elt/locations.csv": {
               "object": "locations"
           }
       }
   }
   return replication_config


def create_sling_resource(env: str):
   # Dynamically generate connection based on enviornment
   connections = [
       SlingConnectionResource(
           name="S3",
           type="s3",
           bucket=EnvVar("AWS_S3_BUCKET"),
           region=EnvVar("AWS_REGION"),
           access_key_id=EnvVar("AWS_ACCESS_KEY_ID"),
           secret_access_key=EnvVar("AWS_SECRET_ACCESS_KEY"),
       )
   ]
   if env == 'LOCAL':
       connections.append(SlingConnectionResource(
           name="DUCKDB",
           type="duckdb",
           instance=f"{DUCKDB_PATH}",
           database="example",
           schema="raw_data",
       ))
   elif env == 'BRANCH':
       connections.append(SlingConnectionResource(
           name="SNOWFLAKE_BRANCH",
           type="snowflake",
           host=EnvVar("SNOWFLAKE_HOST"),
           user=EnvVar("SNOWFLAKE_USER"),
           password=EnvVar("SNOWFLAKE_PASSWORD"),
           role=EnvVar("SNOWFLAKE_ROLE"),
           database="DEMO_DB2_BRANCH",
           schema="RAW_DATA",
       ))
   elif env == 'PROD':
       connections.append(SlingConnectionResource(
           name="SNOWFLAKE_PROD",
           type="snowflake",
           host=EnvVar("SNOWFLAKE_HOST"),
           user=EnvVar("SNOWFLAKE_USER"),
           password=EnvVar("SNOWFLAKE_PASSWORD"),
           role=EnvVar("SNOWFLAKE_ROLE"),
           database="DEMO_DB2",
           schema="RAW_DATA",
       ))
   return SlingResource(connections=connections)


env = get_env()
replication_config = create_replication_config(env)
sling_resource = create_sling_resource(env)
