from dagster_pyspark import pyspark_resource

# The dbt file dbt_project/config/profiles.yaml
# specifies what databases to targets, and locally will
# execute against a DuckDB

# Similar to having different dbt targets, here we create the resource
# configuration by environment


resource_def = {
    "LOCAL": {
        "pyspark": pyspark_resource,
    },
    "BRANCH": {
        "pyspark": pyspark_resource,
    },
    "PROD": {
        "pyspark": pyspark_resource,
    },
}
