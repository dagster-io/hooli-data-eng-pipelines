from hooli_data_eng.defs.pandas import assets as pandas_assets
from hooli_data_eng.defs.pandas.resources import resource_def
from hooli_data_eng.defs.pandas.schedules import (
    predict_job,
    min_order_freshness_check_sensor,
    avg_orders_freshness_check_schedule,
    orders_sensor,
)
from hooli_data_eng.utils import get_env

from pathlib import Path
import dagster as dg
from dagster_cloud.metadata.source_code import link_code_references_to_git_if_cloud

pandas_checks = dg.load_asset_checks_from_modules(
    [pandas_assets],
)

pandas_assets = dg.load_assets_from_modules(
    [pandas_assets],
)

defs = dg.Definitions(
    assets=link_code_references_to_git_if_cloud(
        dg.with_source_code_references(
            [
                *pandas_assets,
            ]
        ),
        file_path_mapping=dg.AnchorBasedFilePathMapping(
            local_file_anchor=Path(__file__),
            file_anchor_path_in_repository="hooli_data_eng/pandas/definitions.py",
        ),
    ),
    asset_checks=[*pandas_checks],
    jobs=[predict_job],
    resources=resource_def[get_env()],
    sensors=[min_order_freshness_check_sensor, orders_sensor],
    schedules=[avg_orders_freshness_check_schedule],
)
