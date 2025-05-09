from hooli_data_eng.defs.custom_ingest import assets as raw_data
from hooli_data_eng.defs.custom_ingest.assets import check_users, raw_data_schema_checks
from hooli_data_eng.defs.custom_ingest.resources import resource_def
from hooli_data_eng.utils import get_env

from pathlib import Path
import dagster as dg
from dagster_cloud.metadata.source_code import link_code_references_to_git_if_cloud

# Our first set of assets represent raw data, and the asset
# definitions can be seen in /assets/raw_data/__init__.py
#
# These raw datasets will be used by dbt as dbt sources
# which can be found in dbt_project/models/sources.yml
raw_data_assets = dg.load_assets_from_modules(
    [raw_data], group_name="RAW_DATA", key_prefix=["RAW_DATA"]
)

defs = dg.Definitions(
    assets=link_code_references_to_git_if_cloud(
        dg.with_source_code_references(
            [
                *raw_data_assets,
            ]
        ),
        file_path_mapping=dg.AnchorBasedFilePathMapping(
            local_file_anchor=Path(__file__),
            file_anchor_path_in_repository="hooli_data_eng/definitions.py",
        ),
    ),
    asset_checks=[
        *raw_data_schema_checks,
        check_users,
    ],
    resources=resource_def[get_env()],
)
