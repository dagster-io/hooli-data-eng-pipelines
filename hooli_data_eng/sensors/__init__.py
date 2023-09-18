from dagster import (
    asset_sensor,
    AssetKey,
    EventLogEntry,
    RunRequest,
    SensorEvaluationContext,
)

from ..jobs import predict_job

# This sensor listens for changes to the orders_augmented asset which
# represents a dbt model. When the table managed by dbt is updated,
# this sensor will trigger the predict_job above, ensuring that anytime
# new order data is produced the forecast is updated
@asset_sensor(asset_key=AssetKey(["ANALYTICS", "orders_augmented"]), job=predict_job)
def orders_sensor(context: SensorEvaluationContext, asset_event: EventLogEntry):
    yield RunRequest(run_key=context.cursor)