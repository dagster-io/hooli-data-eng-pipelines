import json
from typing import Optional, cast

from dagster import (
    AssetKey,
    DagsterEventType,
    EventRecordsFilter,
    JobDefinition,
    RunRequest,
    SensorDefinition,
    asset_sensor,
    check,
)

from ..resources.snowflake_io_manager import generate_asset_key_for_snowflake_table


def make_hn_tables_updated_sensor(
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
        asset_key="hn_tables_updated",
        pipeline_name=pipeline_name,
        name=f"{job_or_pipeline_name}_on_hn_tables_updated",
        mode=mode,
        job=job,
    )
    def hn_tables_updated_sensor(context):
        yield RunRequest(run_key=None)

    return hn_tables_updated_sensor
