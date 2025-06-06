import dagster as dg
from dagster.components import Component, ComponentLoadContext, Resolvable
from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class ScheduledJobComponent(Component, Resolvable):
    """dbt projects with a schedule.

    Adds a Dagster schedule for a given dbt selection string and a cron string.
    """

    # added fields here will define yaml schema via Model
    cron_schedule: str
    asset_selection: str
    job_name: str

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        job = dg.define_asset_job(
            name=self.job_name,
            selection=self.asset_selection,
        )

        schedule = dg.ScheduleDefinition(
            job=job,
            cron_schedule=self.cron_schedule,
        )

        return dg.Definitions(
            schedules=[schedule],
            jobs=[job],
        )


@dataclass
class ScheduledPartitionedJobComponent(Component, Resolvable):
    """dbt projects with a schedule.

    Adds a Dagster schedule for a given dbt selection string and a cron string.
    """

    # added fields here will define yaml schema via Model
    asset_selection: str
    job_name: str
    tags: Optional[dict[str, Any]]

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        job = dg.define_asset_job(
            name=self.job_name,
            selection=self.asset_selection,
            tags=self.tags,
        )
        schedule = dg.build_schedule_from_partitioned_job(job)

        return dg.Definitions(
            schedules=[schedule],
            jobs=[job],
        )
