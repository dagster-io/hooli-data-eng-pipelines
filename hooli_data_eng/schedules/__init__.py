from dagster import schedule, ScheduleEvaluationContext, RunRequest

from hooli_data_eng.jobs import analytics_job


# This schedule tells dagster to run the analytics_job daily
#analytics_schedule = build_schedule_from_partitioned_job(analytics_job)

@schedule(cron_schedule="0 0 * * *", job=analytics_job)
def analytics_schedule(context: ScheduleEvaluationContext):
    return RunRequest(run_key=None, run_config={}, tags={})