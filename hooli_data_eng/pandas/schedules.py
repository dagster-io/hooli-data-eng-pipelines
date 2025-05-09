import dagster as dg
from hooli_data_eng.pandas.assets import (
    min_order_freshness_check,
    avg_orders_freshness_check,
)

# This job selects the predicted_orders asset defined in
# databricks/assets.py
predict_job = dg.define_asset_job(
    "predict_job",
    selection=dg.AssetSelection.keys(["FORECASTING", "predicted_orders"]),
    tags={"alert_team": "ml"},
)


# This sensor listens for changes to the orders_augmented asset which
# represents a dbt model. When the table managed by dbt is updated,
# this sensor will trigger the predict_job above, ensuring that anytime
# new order data is produced the forecast is updated
@dg.asset_sensor(
    asset_key=dg.AssetKey(["ANALYTICS", "orders_augmented"]), job=predict_job
)
def orders_sensor(context: dg.SensorEvaluationContext, asset_event: dg.EventLogEntry):
    yield dg.RunRequest(run_key=context.cursor)


min_order_freshness_check_sensor = dg.build_sensor_for_freshness_checks(
    freshness_checks=min_order_freshness_check, minimum_interval_seconds=10 * 60
)

avg_orders_freshness_check_schedule = dg.ScheduleDefinition(
    name="check_avg_orders_freshness_schdule",
    cron_schedule="*/10 * * * *",
    job=dg.define_asset_job(
        "check_avg_orders_freshness_job",
        selection=dg.AssetSelection.checks(*avg_orders_freshness_check),
    ),
)
