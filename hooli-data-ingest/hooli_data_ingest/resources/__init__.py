import os
from pathlib import Path

from dagster import EnvVar
from dagster_embedded_elt.sling import (
   SlingResource,
   SlingConnectionResource,
)

def get_env():
   if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "") == "1":
       return "BRANCH"
   if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "data-eng-prod":
       return "PROD"
   return "LOCAL"

# Paths for local dev
current_file_path = Path(__file__)
hooli_data_ingest_root = current_file_path.parent.parent.parent
project_root = hooli_data_ingest_root.parent
DUCKDB_PATH = project_root / "dbt_project" / "example.duckdb"
LOCATIONS_CSV_PATH = f"file://{hooli_data_ingest_root}/locations.csv"


if get_env() == "LOCAL":
   replication_config = {
       "source": "LOCAL",
       "target": "DUCKDB",
       "defaults": {
           "mode": "full-refresh",
           "object": "{stream_file_folder}.{stream_file_name}",
           "source_options": {
               "format": "csv"
           }
       },
       "streams": {
           LOCATIONS_CSV_PATH: {
               "object": "locations"
           }
       }
   }

   sling_resource = SlingResource(
       connections=[
            SlingConnectionResource(
                name="Local",
                type="local",
                url=LOCATIONS_CSV_PATH,
            ),
            SlingConnectionResource(
                name="DUCKDB",
                type="duckdb",
                instance=f"{DUCKDB_PATH}",
                database="example",
                schema="raw_data",
            ),
        ]
   )

if get_env() != "LOCAL":
    replication_config = {
        "source": "S3",
        "target": "SNOWFLAKE_PROD" if get_env() == "PROD" else "SNOWFLAKE_BRANCH",
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

    sling_resource = SlingResource(
        connections=[
        SlingConnectionResource(
            name="S3",
            type="s3",
            bucket=EnvVar("AWS_S3_BUCKET"),
            region=EnvVar("AWS_REGION"),
            access_key_id=EnvVar("AWS_ACCESS_KEY_ID"),
            secret_access_key=EnvVar("AWS_SECRET_ACCESS_KEY"),
        ),
        SlingConnectionResource(
            name="SNOWFLAKE_PROD" if get_env() == "PROD" else "SNOWFLAKE_BRANCH",
            type="snowflake",
            host=EnvVar("SNOWFLAKE_HOST"),
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
            role=EnvVar("SNOWFLAKE_ROLE"),
            database="DEMO_DB2" if get_env() == "PROD" else "DEMO_DB2_BRANCH",
            schema="RAW_DATA",
        )
        ]
    )