from dagster import build_schedule_from_partitioned_job

from hooli_data_eng.jobs import analytics_job

# This schedule tells dagster to run the analytics_job daily
analytics_schedule = build_schedule_from_partitioned_job(analytics_job)