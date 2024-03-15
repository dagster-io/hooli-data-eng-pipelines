from dagster import AutoMaterializePolicy, AssetExecutionContext, DataVersion, asset, observable_source_asset
import os
import pandas as pd
import time


#uses a cron entry to run every minute that updates files every 30 seconds (two exeuctions)
@observable_source_asset(
    key="observable_source_asset_key",
    description="Observes changes in an external data source",
    auto_observe_interval_minutes=.5)
def source_file():
    return DataVersion(str(os.path.getmtime("/Users/christian/code/hooli-data-eng-pipelines/my_observable_asset.csv")))


@asset(
    deps=[source_file],
    auto_materialize_policy=AutoMaterializePolicy.eager(),   
)
def asset_that_depends_on_source(context: AssetExecutionContext) -> int:
    context.log.info("asset starts")
    time.sleep(35)
    context.log.info("asset completes")
    return 1
    