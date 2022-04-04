from typing import Optional, cast

from dagster import (AssetKey, JobDefinition, RunRequest, SensorDefinition,
                     asset_sensor, check)


def make_hacker_news_tables_sensor(
    job: Optional[JobDefinition] = None,
    pipeline_name: Optional[str] = None,  # legacy arg
    mode: Optional[str] = None,  # legacy arg
) -> SensorDefinition:
    """
    Returns a sensor that launches the given job when the HN "comments" and "stories" tables have
    both been updated.
    """
    check.invariant(job is not None or pipeline_name is not None)
    job_or_pipeline_name = cast(str, job.name if job else pipeline_name)

    @asset_sensor(
        asset_key=AssetKey("hacker_news_tables"),
        pipeline_name=pipeline_name,
        name=f"{job_or_pipeline_name}_on_hacker_news_tables",
        mode=mode,
        job=job,
    )
    def hacker_news_tables_sensor(_context, _event):
        yield RunRequest(run_key=None)

    return hacker_news_tables_sensor
