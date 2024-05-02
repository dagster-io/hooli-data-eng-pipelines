from dagster import (
     AutoMaterializePolicy, AssetExecutionContext, DataVersion, asset, observable_source_asset, SourceAsset,
 MaterializeResult, 
 TableColumnDep,
 AssetKey,
 TableColumnLineage,
)
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


# Define the source asset
my_source_asset = SourceAsset(key="my_source_asset")

# Define the dependent asset
@asset(
    deps=["my_source_asset"],
)
def dependent_asset() -> MaterializeResult:
    return MaterializeResult(
        metadata={
            "dagster/column_lineage": TableColumnLineage(
                deps_by_column={
                    "new_column_foo": [
                        TableColumnDep(
                            asset_key=AssetKey("my_source_asset"),
                            column_name="column_bar",
                        ),
                        TableColumnDep(
                            asset_key=AssetKey("my_source_asset"),
                            column_name="column_baz",
                        ),
                    ],
                    "new_column_qux": [
                        TableColumnDep(
                            asset_key=AssetKey("my_source_asset"),
                            column_name="column_quuz",
                        ),
                    ],
                }
            )
        }
    )

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
    

@asset(
    deps=["observable_source_asset_key"],
    auto_materialize_policy=AutoMaterializePolicy.eager(),   
)
def asset_2_that_depends_on_source(context: AssetExecutionContext) -> pd.DataFrame:
    context.log.info("asset starts")
    time.sleep(35)
    df = pd.read_csv(USERS_CSV_PATH)
    context.log.info("asset completes")
    return df[df["second_column"] == 3]