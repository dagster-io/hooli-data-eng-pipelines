from dagster import repository, schedule_from_partitions

from .jobs import dbt_prod_job, ingest_hacker_news_job

# from .schedules import hourly_hn_download_schedule
from .sensors import make_hn_tables_updated_sensor


@repository
def prod_repo():
    return [
        make_hn_tables_updated_sensor(dbt_prod_job),
        schedule_from_partitions(ingest_hacker_news_job),
        # hourly_hn_download_schedule,
    ]
