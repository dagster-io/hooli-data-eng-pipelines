from dagster import ScheduleDefinition

from ..jobs import salesforce_ingest

daily_salesforce_ingest = ScheduleDefinition(
    name="daily_salesforce_ingest",
    cron_schedule="0 17 * * *",
    job=salesforce_ingest,
    description="Daily Fivetran ingest from Salesforce",
)
