from pathlib import Path

from dagster import (
    AnchorBasedFilePathMapping,
    Definitions,
    with_source_code_references
)

from dagster_cloud.metadata.source_code import link_code_references_to_git_if_cloud

from hooli_bi.powerbi_assets import powerbi_assets  # noqa: TID252
from hooli_bi.powerbi_workspace import power_bi_workspace

defs = Definitions(
    assets=link_code_references_to_git_if_cloud(
        with_source_code_references([*powerbi_assets]),
        file_path_mapping=AnchorBasedFilePathMapping(
            local_file_anchor=Path(__file__),
            file_anchor_path_in_repository="hooli-bi/hooli_bi/definitions.py",
        ),
    ),
    resources={"power_bi": power_bi_workspace},
)
