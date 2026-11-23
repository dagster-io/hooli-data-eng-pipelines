from pathlib import Path

import dagster as dg


@dg.definitions
def defs() -> dg.Definitions:
    return dg.load_from_defs_folder(path_within_project=Path(__file__).parent)
