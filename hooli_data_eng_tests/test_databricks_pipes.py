from dagster import materialize
from hooli_data_eng.assets.forecasting import databricks_asset
from hooli_data_eng.resources import client
from dagster_databricks import PipesDatabricksClient

# to meaningfully run this test you must set
# DAGSTER_CLOUD_DEPLOYMENT_NAME="data-eng-prod"  
# and also set
# DATABRICKS_HOST="your host"
# DATABRICKS_TOKEN="your token"

result = materialize(
    [databricks_asset],
    resources={
        "pipes_client": PipesDatabricksClient(
            client,
        )
    },
    raise_on_error=False,
)