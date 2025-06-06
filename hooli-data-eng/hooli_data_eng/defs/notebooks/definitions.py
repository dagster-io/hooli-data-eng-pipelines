from hooli_data_eng.defs.notebooks import assets as notebooks_assets
from hooli_data_eng.defs.notebooks.resources import resource_def
from hooli_data_eng.utils import get_env

from pathlib import Path
import dagster as dg
from dagster_cloud.metadata.source_code import link_code_references_to_git_if_cloud


notebooks_assets = dg.load_assets_from_modules(
    [notebooks_assets], group_name="FORECASTING"
)

defs = dg.Definitions(
    assets=link_code_references_to_git_if_cloud(
        dg.with_source_code_references(
            [
                *notebooks_assets,
            ]
        ),
        file_path_mapping=dg.AnchorBasedFilePathMapping(
            local_file_anchor=Path(__file__),
            file_anchor_path_in_repository="hooli_data_eng/notebooks/definitions.py",
        ),
    ),
    resources=resource_def[get_env()],
)
