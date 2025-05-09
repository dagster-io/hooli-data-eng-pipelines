from pathlib import Path
import dagster as dg
from dagster_cloud.metadata.source_code import link_code_references_to_git_if_cloud
from hooli_data_eng.dbt import assets
from hooli_data_eng.dbt.resources import resource_def
from hooli_data_eng.dbt.schedules import (
    weekly_freshness_check_sensor,
    dbt_slim_ci_job,
    dbt_code_version_sensor,
    analytics_job,
    analytics_schedule,
)
from hooli_data_eng.utils import get_env

dbt_assets = dg.load_assets_from_modules([assets])

dbt_schema_checks = dg.build_column_schema_change_checks(assets=[*dbt_assets])

dbt_asset_checks = dg.load_asset_checks_from_modules([assets])

defs = dg.Definitions(
    assets=link_code_references_to_git_if_cloud(
        dg.with_source_code_references([*dbt_assets]),
        file_path_mapping=dg.AnchorBasedFilePathMapping(
            local_file_anchor=Path(__file__),
            file_anchor_path_in_repository="hooli_data_eng/dbt/definitions.py",
        ),
    ),
    asset_checks=[*dbt_asset_checks, *dbt_schema_checks],
    resources=resource_def[get_env()],
    jobs=[analytics_job, dbt_slim_ci_job],
    schedules=[analytics_schedule],
    sensors=[weekly_freshness_check_sensor, dbt_code_version_sensor],
)
