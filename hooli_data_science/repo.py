from dagster import repository

from .jobs import dbt_prod_job, dbt_staging_job, download_prod_job, download_staging_job


@repository
def prod_repo():
    return [dbt_prod_job, download_prod_job]


@repository
def staging_repo():
    return [dbt_staging_job, download_staging_job]
