from dagster import ScheduleDefinition

from ..jobs import salesforce_ingest

from ..assets import hacker_news_assets


def not_on_weekends(context):
    return context.scheduled_execution_time.isoweekday() < 6


daily_salesforce_ingest = ScheduleDefinition(
    name="daily_salesforce_ingest",
    cron_schedule="0 17 * * *",
    job=salesforce_ingest,
    description="Daily Fivetran ingest from Salesforce",
    should_execute=not_on_weekends,
)

hourly_hn_assets = ScheduleDefinition(
    name="hourly_hn_assets",
    cron_schedule="0 */2 * * *",
    job=hacker_news_assets,
    description="Hourly HackerNews ELT",
    should_execute=not_on_weekends,
)
