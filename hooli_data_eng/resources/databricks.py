from dagster_databricks import databricks_pyspark_step_launcher
from pathlib import Path

db_step_launcher = databricks_pyspark_step_launcher.configured({
    
        "run_config": {
            "run_name": "launch_step",
            "cluster": {"existing": "1012-194900-4d22jaa1"},
            "libraries": [  
                {"pypi": {"package": "dagster-aws"}},
                {"pypi": {"package": "dagster-pandas"}},
                {"pypi": {"package": "dagster-dbt"}},
                {"pypi": {"package": "dagster-duckdb"}},
                {"pypi": {"package": "dagster-duckdb-pandas"}},
                {"pypi": {"package": "dbt-core"}},
                {"pypi": {"package": "dbt-snowflake"}},
                {"pypi": {"package": "dagster-cloud"}},
                {"pypi": {"package": "pandas>=1.4.0"}},
                {"pypi": {"package": "snowflake-sqlalchemy"}},
                {"pypi": {"package": "requests"}},
            ],
        },
        "databricks_host": {"env": "DATABRICKS_HOST"},
        "databricks_token": {"env": "DATABRICKS_TOKEN"},
        "local_pipeline_package_path": str(Path(__file__).parent.parent),
        "secrets_to_env_variables": [
            {"name": "SNOWFLAKE_USER", "key": "snowflake_user", "scope": "dagster-test"},
            {"name": "SNOWFLAKE_PASSWORD", "key": "snowflake_password", "scope": "dagster-test"},
            {"name": "SNOWFLAKE_ACCOUNT", "key": "snowflake_account", "scope": "dagster-test"},
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