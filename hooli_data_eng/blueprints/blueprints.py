# from pathlib import Path
# from typing import Literal, Optional

# from dagster import define_asset_job, Definitions, ScheduleDefinition
# from dagster_blueprints import YamlBlueprintsLoader
# from dagster_blueprints.blueprint import Blueprint
# from dagster_dbt import build_dbt_asset_selection

# from hooli_data_eng.assets.dbt_assets import daily_dbt_assets

# # This class is used to construct dbt jobs via yaml files


# class DbtSelectScheduledJobBlueprint(Blueprint):
#     type: Literal["dbt_select_job"]
#     name: str
#     select: str
#     exclude: Optional[str]
#     cron: str

#     def build_defs(self) -> Definitions:
#         job_def = define_asset_job(
#             name=self.name,
#             selection=build_dbt_asset_selection(
#                 [daily_dbt_assets], dbt_select=self.select, dbt_exclude=self.exclude
#             ),
#         )
#         schedule_def = ScheduleDefinition(job=job_def, cron_schedule=self.cron)
#         return Definitions(schedules=[schedule_def])


# # The loader will pick up any yaml files in the blueprints_jobs directory
# loader = YamlBlueprintsLoader(
#     per_file_blueprint_type=DbtSelectScheduledJobBlueprint,
#     path=Path(__file__).parent / "blueprints_jobs",
# )
