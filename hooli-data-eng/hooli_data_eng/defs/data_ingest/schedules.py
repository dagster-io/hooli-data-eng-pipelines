from dagster import ScheduleDefinition

from hooli_data_eng.defs.data_ingest.jobs import daily_sling_job

daily_sling_assets = ScheduleDefinition(
    job=daily_sling_job,
    cron_schedule="0 0 * * *",  # every day at midnight
)
