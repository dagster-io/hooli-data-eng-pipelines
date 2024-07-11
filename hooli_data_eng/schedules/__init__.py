from dagster import build_schedule_from_partitioned_job, schedule, SkipReason

from hooli_data_eng.jobs import analytics_job

# This schedule tells dagster to run the analytics_job daily
analytics_schedule = build_schedule_from_partitioned_job(analytics_job)

@schedule(job=analytics_job, cron_schedule="* * * * *")
def logs_then_skips(context):
    context.log.info("Logging from a schedule!")
    return SkipReason("Nothing to do")