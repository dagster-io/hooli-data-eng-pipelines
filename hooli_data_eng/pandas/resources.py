from hooli_data_eng.resources import snowflake_branch_io_manager, snowflake_prod_io_manager, duckdb_io_manager

# The dbt file dbt_project/config/profiles.yaml
# specifies what databases to targets, and locally will
# execute against a DuckDB

# Similar to having different dbt targets, here we create the resource
# configuration by environment

resource_def = {
    "LOCAL": {
        "io_manager": duckdb_io_manager,
        
    },
    "BRANCH": {
        "io_manager": snowflake_branch_io_manager,
    },
    "PROD": {
        "io_manager": snowflake_prod_io_manager,
}
}
