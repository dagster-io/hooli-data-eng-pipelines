from dagster import AutoMaterializePolicy, AssetExecutionContext, DataVersion, asset, observable_source_asset
from dagster._utils import file_relative_path
import os
import pandas as pd
import time
from pathlib import Path

USERS_CSV_PATH = Path(os.getcwd(), 'my_observable_asset.csv')
# for some inscrutable reason file_relative_path isnt' working.
#file_relative_path(__file__, "../my_observable_asset.csv")

#uses a cron entry to run every minute that updates files every 30 seconds (two exeuctions)
@observable_source_asset(
    key="observable_source_asset_key",
    description="Observes changes in an external data source",
    auto_observe_interval_minutes=.5)
def source_file():
    return DataVersion(str(os.path.getmtime(USERS_CSV_PATH)) )


@asset(
    deps=["observable_source_asset_key"],
    auto_materialize_policy=AutoMaterializePolicy.eager(),   
)
def asset_that_depends_on_source(context: AssetExecutionContext) -> pd.DataFrame:
    context.log.info("asset starts")
    time.sleep(35)
    df = pd.read_csv(USERS_CSV_PATH)
    context.log.info("asset completes")
    return df[df["first_column"] == 1]
    