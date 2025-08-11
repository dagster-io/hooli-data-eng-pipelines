import os
from dagster_duckdb_pandas import DuckDBPandasIOManager
from dagster_snowflake_pandas import SnowflakePandasIOManager
import dagster as dg
from hooli_data_eng.defs.dbt.resources import DBT_PROJECT_DIR
from dagster_duckdb import DuckDBResource
from dagster_snowflake import SnowflakeResource
from hooli_data_eng.utils import get_env

# The dbt file dbt_project/config/profiles.yaml
# specifies what databases to targets, and locally will
# execute against a DuckDB

# Similar to having different dbt targets, here we create the resource
# configuration by environment

duckdb_io_manager = DuckDBPandasIOManager(
    database=os.path.join(DBT_PROJECT_DIR, "example.duckdb")
)

snowflake_branch_io_manager = SnowflakePandasIOManager(
    database="DEMO_DB2_BRANCH",
    account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
    user=dg.EnvVar("SNOWFLAKE_USER"),
    password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
    warehouse="TINY_WAREHOUSE",
)

snowflake_prod_io_manager = SnowflakePandasIOManager(
    database="DEMO_DB2",
    account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
    user=dg.EnvVar("SNOWFLAKE_USER"),
    password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
    warehouse="TINY_WAREHOUSE",
)

duckdb_resource = DuckDBResource(database=os.path.join(DBT_PROJECT_DIR, "example.duckdb"))

snowflake_branch_resource =  SnowflakeResource(
    database="DEMO_DB2_BRANCH",
    account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
    user=dg.EnvVar("SNOWFLAKE_USER"),
    password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
    warehouse="TINY_WAREHOUSE",
)

snowflake_prod_resource =  SnowflakeResource(
    database="DEMO_DB2",
    account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
    user=dg.EnvVar("SNOWFLAKE_USER"),
    password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
    warehouse="TINY_WAREHOUSE",
)

resource_def = {
    "LOCAL": {
        "db_resource": duckdb_resource,
    },
    "BRANCH": {
        "db_resource": snowflake_branch_resource,
    },
    "PROD": {
        "db_resource": snowflake_prod_resource,
    },
}

def get_resource_for_env():
    return resource_def[get_env()]