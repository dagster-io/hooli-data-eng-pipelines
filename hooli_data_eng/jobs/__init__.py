from dagster import AssetSelection, define_asset_job

# With assets defined we have everything to run Dagster
# ourselves if we wanted to manually create assets.
# Most of the time you will want to automate asset creation.
# In dagster, jobs allow you to update all or some assets.
# Jobs can be run on a schedule, or in response to an external
# event using a sensor.

# This job updates all of the assets upstream of "orders_augmented",
# which is an asset representing a model in dbt
analytics_job = define_asset_job(
    name="refresh_analytics_model_job",
    selection=AssetSelection.keys(["ANALYTICS", "orders_augmented"]).upstream()
    - AssetSelection.keys(["CLEANED", "locations_cleaned"]),
    tags={"dagster/max_retries": "1"},
    # config = {"execution": {"config": {"multiprocess": {"max_concurrent": 1}}}}
)

# This job selects the predicted_orders asset defined in
# assets/forecasting/__init__.py
predict_job = define_asset_job(
    "predict_job",
    selection=AssetSelection.keys(["FORECASTING", "predicted_orders"]),
    tags={"alert_team": "ml"},
)
