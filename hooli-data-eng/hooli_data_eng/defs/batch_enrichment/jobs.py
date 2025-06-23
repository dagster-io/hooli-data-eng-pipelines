from dagster import (
    AssetSelection,
    ScheduleDefinition,
    define_asset_job,
)

# define a job and schedule to run the pipeline
# alternatively could use freshness policies and auto-materialization, partitions, or other ways to orient the schedule
run_assets_job = define_asset_job(
    name="run_etl_pipeline",
    selection=AssetSelection.all(),
    tags={"dagster/max_retries": "1"},
)

run_assets_30min = ScheduleDefinition(
    name="run_assets_30min", job=run_assets_job, cron_schedule="*/30 * * * *"
)
