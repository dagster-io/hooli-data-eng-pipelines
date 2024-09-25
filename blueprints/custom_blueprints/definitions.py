import tempfile
from pathlib import Path
from subprocess import Popen
from typing import Literal
from typing import Optional

from dagster import Definitions, asset, define_asset_job, AssetExecutionContext, ScheduleDefinition
from dagster_blueprints import YamlBlueprintsLoader
from dagster_blueprints.blueprint import Blueprint
from dagster_dbt import build_dbt_asset_selection, dbt_assets, DbtCliResource
from hooli_data_eng.resources import dbt_project

DBT_MANIFEST = dbt_project.manifest_path

@dbt_assets(
    manifest=DBT_MANIFEST,
    project=dbt_project,
    )
def dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()

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
                [dbt_assets], dbt_select=self.select, dbt_exclude=self.exclude
            ),
        )
        schedule_def = ScheduleDefinition(job=job_def, cron_schedule=self.cron)
        return Definitions(schedules=[schedule_def])


loader = YamlBlueprintsLoader(
    per_file_blueprint_type=DbtSelectScheduledJobBlueprint,
    path=Path(__file__).parent / "dbt_bp_assets",
)
defs = Definitions.merge(loader.load_defs(), Definitions(assets=[dbt_assets]))