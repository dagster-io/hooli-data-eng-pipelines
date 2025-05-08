import pandas as pd

import dagster as dg
from dagstermill import define_dagstermill_asset
from dagster._core.definitions.tags import build_kind_tag
from dagster._utils import file_relative_path

from hooli_data_eng.utils.kind_helpers import get_kind

# dynamically determine storage_kind based on environment
storage_kind = get_kind()



# This asset uses a Jupyter Notebook which takes inputs from the warehouse
# and the trained model coefficients
model_nb = define_dagstermill_asset(
    name="model_nb",
    notebook_path=file_relative_path(__file__, "model.ipynb"),
    ins={
        "weekly_order_summary": dg.AssetIn(
            key_prefix=["ANALYTICS"], dagster_type=pd.DataFrame
        ),
        "order_forecast_model": dg.AssetIn(),
    },
    required_resource_keys={"io_manager"},
    asset_tags={**build_kind_tag("S3")},
)


