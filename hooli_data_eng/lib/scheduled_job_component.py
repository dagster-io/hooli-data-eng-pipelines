import dagster as dg
from dagster.components import Component, ComponentLoadContext, Resolvable
from dataclasses import dataclass


@dataclass
class ScheduledJobComponent(Component, Resolvable):
    """dbt projects with a schedule.

    Adds a Dagster schedule for a given dbt selection string and a cron string.
    """

    # added fields here will define yaml schema via Model
    cron_schedule: str
    dagster_selection: str
    job_name: str

    def __init__(
        self, cron_schedule: str, dagster_selection: str, job_name: str, **kwargs
    ):
        self.cron_schedule = cron_schedule
        self.dagster_selection = dagster_selection
        self.job_name = job_name

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        # selection='key:"raw_data_b"+ and +key:"summary_stats_2"'

        job = dg.define_asset_job(
            name=self.job_name,
            selection=self.dagster_selection,
        )

        schedule = dg.ScheduleDefinition(
            job=job,
            cron_schedule=self.cron_schedule,
        )

        return dg.Definitions(
            schedules=[schedule],
            jobs=[job],
        )
