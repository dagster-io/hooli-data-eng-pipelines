import tempfile
from pathlib import Path
from subprocess import Popen
from typing import Literal
from typing import Optional

from dagster import Definitions, asset, define_asset_job
from dagster_blueprints import YamlBlueprintsLoader
from dagster_blueprints.blueprint import Blueprint
from dagster_dbt import build_dbt_asset_selection

class DbtSelectScheduledJobBlueprint(Blueprint):
    type: Literal["dbt_select_job"]
    name: str
    select: str
    exclude: Optional[str]
    cron: str

    def build_defs(self) -> Definitions:
        job_def = define_asset_job(
            name=self.name,
            selection=build_dbt_asset_selection(
                [cleaned_assets], dbt_select=self.select, dbt_exclude=self.exclude
            ),
        )
        schedule_def = ScheduleDefinition(job=job_def, cron_schedule=self.cron)
        return Definitions(scheduled=[schedule_def])


loader = YamlBlueprintsLoader(
    per_file_blueprint_type=DbtSelectScheduledJobBlueprint,
    path=Path(__file__).parent / "dbt_assets",
)
defs = loader.load_defs()