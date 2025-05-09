from hooli_data_eng.files import assets as files_assets
from hooli_data_eng.files.resources import resource_def
from hooli_data_eng.files.sensors import watch_s3_sensor
from hooli_data_eng.utils import get_env

from pathlib import Path
import dagster as dg
from dagster_cloud.metadata.source_code import link_code_references_to_git_if_cloud

# Our first set of assets represent raw data, and the asset
# definitions can be seen in /assets/raw_data/__init__.py
#
# These raw datasets will be used by dbt as dbt sources
# which can be found in dbt_project/models/sources.yml
files_assets = dg.load_assets_from_modules([files_assets], group_name="FORECASTING")

defs = dg.Definitions(
    assets=link_code_references_to_git_if_cloud(
        dg.with_source_code_references(
            [
                *files_assets,
            ]
        ),
        file_path_mapping=dg.AnchorBasedFilePathMapping(
            local_file_anchor=Path(__file__),
            file_anchor_path_in_repository="hooli_data_eng/files/definitions.py",
        ),
    ),
    resources=resource_def[get_env()],
    sensors=[watch_s3_sensor],
)
