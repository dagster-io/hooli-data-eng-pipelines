from dagster import AssetSelection, define_asset_job

raw_location_by_day = AssetSelection.keys("raw_location")

daily_sling_job = define_asset_job(
    name="daily_sling_job",
    selection=raw_location_by_day,
)