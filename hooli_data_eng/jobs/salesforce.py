from dagster_fivetran import fivetran_resource, fivetran_sync_op
from dagster_dbt import dbt_cloud_resource, dbt_cloud_run_op
from dagster import job
import os

FIVETRAN_SALESFORCE_SYNC_ID = "conjure_constitutional"
DBT_CLOUD_SALESFORCE_JOB_ID = 42476

ingest_salesforce = fivetran_sync_op.configured(
    {"connector_id": FIVETRAN_SALESFORCE_SYNC_ID}, name="ingest_salesforce"
)

aggregate_salesforce = dbt_cloud_run_op.configured(
    {"job_id": DBT_CLOUD_SALESFORCE_JOB_ID}, name="aggregate_salesforce"
)


@job(
    resource_defs={
        "dbt_cloud": dbt_cloud_resource,
        "fivetran": fivetran_resource,
    },
    config={
        "resources": {
            "dbt_cloud": {
                "config": {
                    "auth_token": {"env": "DBT_CLOUD_AUTH_TOKEN"},
                    "account_id": int(os.getenv("DBT_CLOUD_ACCOUNT_ID")),
                }
            },
            "fivetran": {
                "config": {
                    "api_key": {"env": "FIVETRAN_API_KEY"},
                    "api_secret": {"env": "FIVETRAN_API_SECRET"},
                }
            },
        },
    },
)
def salesforce_ingest():
    aggregate_salesforce(start_after=ingest_salesforce())
