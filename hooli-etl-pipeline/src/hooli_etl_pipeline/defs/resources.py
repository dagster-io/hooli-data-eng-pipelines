from dagster_duckdb import DuckDBResource
from dagster_snowflake import SnowflakeResource
import os
import dagster as dg
import pandas as pd


def get_env():
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "data-eng-prod":
        return "PROD"
    if os.getenv("DAGSTER_IS_DEV_CLI"):
        return "LOCAL"
    # default to BRANCH so we use that in github CI
    return "BRANCH"


def get_database_kind():
    if get_env() == "PROD":
        return "snowflake"
    elif get_env() == "BRANCH":
        return "snowflake"
    else:
        return "duckdb"

import dagster as dg
import pandas as pd
from dagster_snowflake import SnowflakeResource
from dagster_duckdb import DuckDBResource
import os



class DataImportResource(dg.ConfigurableResource):
    """Resource for importing data from URLs to databases"""
    
    def import_url_to_database(self, url: str, table_name: str, database_resource):
        """Import data from URL to the specified database resource"""
        # Read data from URL
        df = pd.read_csv(url)
        
        # Determine database type and import accordingly
        if isinstance(database_resource, SnowflakeResource):
            self._import_to_snowflake(df, table_name, database_resource)
        elif isinstance(database_resource, DuckDBResource):
            self._import_to_duckdb(df, table_name, database_resource)
        else:
            raise ValueError(f"Unsupported database resource type: {type(database_resource)}")
    
    def _import_to_snowflake(self, df: pd.DataFrame, table_name: str, snowflake_resource: SnowflakeResource):
        """Import DataFrame to Snowflake"""
        with snowflake_resource.get_connection() as conn:
            from snowflake.connector.pandas_tools import write_pandas
            write_pandas(conn, df, table_name=table_name, auto_create_table=True, overwrite=True, quote_identifiers=False)
    
    def _import_to_duckdb(self, df: pd.DataFrame, table_name: str, duckdb_resource: DuckDBResource):
        """Import DataFrame to DuckDB"""
        with duckdb_resource.get_connection() as conn:
            conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")


resource_def = {
        "LOCAL": {
            "database": DuckDBResource(
                database="/tmp/jaffle_platform.duckdb"
            ),
            "data_importer": DataImportResource(),
        },
        "BRANCH": {
            "database": SnowflakeResource(
                database="DEMO_DB2_BRANCH",
                schema=dg.EnvVar("SNOWFLAKE_SCHEMA"),
                account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
                user=dg.EnvVar("SNOWFLAKE_USER"),
                password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
                warehouse="TINY_WAREHOUSE",
            ),
            "data_importer": DataImportResource(),
        },
        "PROD": {
            "database": SnowflakeResource(
                database="DEMO_DB2",
                schema=dg.EnvVar("SNOWFLAKE_SCHEMA"),
                account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
                user=dg.EnvVar("SNOWFLAKE_USER"),
                password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
                warehouse="TINY_WAREHOUSE",
            ),
            "data_importer": DataImportResource(),
        }
}


@dg.definitions
def resources():
    return dg.Definitions(
        resources=resource_def[get_env()],
    )

print(get_env())