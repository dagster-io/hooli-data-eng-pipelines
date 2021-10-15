from dagster import repository, schedule_from_partitions

from .jobs import dbt_prod_job, dbt_staging_job, download_prod_job, download_staging_job
from .schedules import hourly_hn_download_schedule
from .sensors import make_hn_tables_updated_sensor


@repository
def prod_repo():
    return [
        make_hn_tables_updated_sensor(dbt_prod_job),
        schedule_from_partitions(download_prod_job),
        hourly_hn_download_schedule,
    ]


@repository
def staging_repo():
    return [
        make_hn_tables_updated_sensor(dbt_staging_job),
        schedule_from_partitions(download_staging_job),
    ]
