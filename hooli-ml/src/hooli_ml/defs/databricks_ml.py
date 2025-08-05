# hooli-ml/databricks_mlops/dagster_pipeline.py
import dagster as dg
from hooli_ml.defs.resources import get_env


# TODO show how you could create "jobs" in databricks based on collections of notebook tasks here for a Job Cluster
# make Notebooks into components
# show how you could make a DatabricksJobComponent


class DatabricksBatchInferenceConfig(dg.Config):
    model_type: str = "RandomForest"
    input_table_name: str = (
        f"{get_env()}.databricks_mlops.feature_store_inference_input"
    )
    output_table_name: str = f"{get_env()}.databricks_mlops.predictions"


class DatabricksFeatureEngineeringDropOffConfig(dg.Config):
    model_type: str = "RandomForest"
    training_data_path: str = "/databricks-datasets/nyctaxi-with-zipcodes/subsampled"
    experiment_name: str = f"/{get_env()}-databricks_mlops-experiment"
    model_name: str = f"{get_env}.databricks_mlops.databricks_mlops-model"
    pickup_features_table: str = f"{get_env()}.databricks_mlops.trip_pickup_features"
    dropoff_features_table: str = f"{get_env()}.databricks_mlops.trip_dropoff_features"
    input_start_date: str = ""
    input_end_date: str = ""
    timestamp_column: str = "tpep_dropoff_datetime"
    output_table_name: str = f"{get_env()}.databricks_mlops.trip_dropoff_features"
    features_transform_module: str = "dropoff_features"
    primary_keys: str = "zip"


class DatabricksFeatureEngineeringPickUpConfig(dg.Config):
    model_type: str = "RandomForest"
    training_data_path: str = "/databricks-datasets/nyctaxi-with-zipcodes/subsampled"
    experiment_name: str = f"/{get_env()}-databricks_mlops-experiment"
    model_name: str = f"{get_env}.databricks_mlops.databricks_mlops-model"
    pickup_features_table: str = f"{get_env()}.databricks_mlops.trip_pickup_features"
    dropoff_features_table: str = f"{get_env()}.databricks_mlops.trip_dropoff_features"
    input_start_date: str = ""
    input_end_date: str = ""
    timestamp_column: str = "tpep_pickup_datetime"
    output_table_name: str = f"{get_env()}.databricks_mlops.trip_pickup_features"
    features_transform_module: str = "pickup_features"
    primary_keys: str = "zip"


class DatabricksModelTrainingConfig(dg.Config):
    training_data_path: str = "/databricks-datasets/nyctaxi-with-zipcodes/subsampled"
    experiment_name: str = f"/{get_env()}-databricks_mlops-experiment"
    model_name: str = f"{get_env}.databricks_mlops.databricks_mlops-model"
    pickup_features_table: str = f"{get_env()}.databricks_mlops.trip_pickup_features"
    dropoff_features_table: str = f"{get_env()}.databricks_mlops.trip_dropoff_features"


class DatabricksModelValidationConfig(dg.Config):
    training_data_path: str = "/databricks-datasets/nyctaxi-with-zipcodes/subsampled"
    run_mode: str = "dry_run"
    enable_baseline_comparison: bool = False
    validation_input: str = "SELECT * FROM delta.`dbfs:/databricks-datasets/nyctaxi-with-zipcodes/subsampled`"
    model_type: str = "regressor"
    targets: str = "fare_amount"
    custom_metrics_loader_function: str = "custom_metrics"
    validation_thresholds_loader_function: str = "validation_thresholds"
    evaluator_config_loader_function: str = "evaluator_config"


class DatabricksModelDeploymentConfig(dg.Config):
    env: str = get_env()


class DatabricksMetricsMonitoringConfig(dg.Config):
    env: str = get_env()
    table_name_under_monitor: str = f"{get_env()}.databricks_mlops.predictions"
    metric_to_monitor: str = "root_mean_squared_error"
    metric_violation_threshold: int = 100
    num_evaluation_windows: int = 5
    num_violation_windows: int = 2


NOTEBOOK_ROOT_PATH = (
    "/Users/christian@dagsterlabs.com/.bundle/databricks_mlops/dev/files/"
)

# @dg.asset(name = "succeed", kinds={"databricks", "feature_engineering"})
# def feature_engineering_pickup(context: dg.AssetExecutionContext, databricks_resource: DatabricksResource, config: DatabricksFeatureEngineeringPickUpConfig):
#     run_id = databricks_resource.run_and_stream_notebook_logs_sdk(
#         notebook_path=NOTEBOOK_ROOT_PATH + "feature_engineering/notebooks/GenerateAndWriteFeatures",
#         parameters={"model_type": config.model_type,
#                     "training_data_path": config.training_data_path,
#                     "model_name": config.model_name,
#                     "pickup_features_table": config.pickup_features_table,
#                     "dropoff_features_table": config.dropoff_features_table,
#         },
#     )
#     context.log.info(f"Feature engineering notebook submitted. Run ID: {run_id}")

# @dg.asset(kinds={"databricks", "feature_engineering"})
# def feature_engineering_dropoff(context: dg.AssetExecutionContext, databricks_resource: DatabricksResource, config: DatabricksFeatureEngineeringPickUpConfig):
#     run_id = databricks_resource.run_and_stream_notebook_logs_sdk(
#         notebook_path=NOTEBOOK_ROOT_PATH + "feature_engineering/notebooks/GenerateAndWriteFeatures",
#         parameters={"model_type": config.model_type,
#                     "training_data_path": config.input_table_path,
#                     "model_name": config.model_name,
#                     "pickup_features_table": config.pickup_features_table,
#                     "dropoff_features_table": config.dropoff_features_table,
#         },
#     )
#     context.log.info(f"Feature engineering notebook submitted. Run ID: {run_id}")

# @dg.asset(name = "fail", deps=[feature_engineering_pickup, "feature_engineering_dropoff"],
#        kinds={"databricks", "training"})
# def model_training(context: dg.AssetExecutionContext, databricks_resource: DatabricksResource, config: DatabricksModelTrainingConfig):
#     run_id = databricks_resource.run_and_stream_notebook_logs_sdk(
#         notebook_path=NOTEBOOK_ROOT_PATH + "training/notebooks/TrainWithFeatureStore",
#         parameters={"training_data_path": config.training_data_path,
#                     "model_name": config.model_name,
#                     "experiment_name": config.experiment_name,
#                     "pickup_features_table": config.pickup_features_table,
#                     "dropoff_features_table": config.dropoff_features_table,
#         }
#     )
#     context.log.info(f"Model training notebook submitted. Run ID: {run_id}")

# @dg.asset(name="real_fail",deps=[feature_engineering_pickup, "feature_engineering_dropoff", model_training],
#        kinds={"databricks", "training"})
# def model_validation(context: dg.AssetExecutionContext, databricks_resource: DatabricksResource, config: DatabricksModelValidationConfig):
#     run_id = databricks_resource.run_and_stream_notebook_logs_sdk(
#         notebook_path=NOTEBOOK_ROOT_PATH + "validation/ModelValidation/",
#         parameters={"run_mode": config.run_mode,
#                     "enable_baseline_comparison": config.enable_baseline_comparison,
#                     "validation_input": config.validation_input,
#                     "model_type": config.model_type,
#                     "targets": config.targets,
#                     "custom_metrics_loader_function": config.custom_metrics_loader_function,
#                     "validation_thresholds_loader_function": config.validation_thresholds_loader_function,
#                     "evaluator_config_loader_function": config.evaluator_config_loader_function
#         }
#     )
#     context.log.info(f"Model training notebook submitted. Run ID: {run_id}")

# @dg.asset(deps=[feature_engineering_pickup, feature_engineering_dropoff, model_training, model_validation],
#        kinds={"databricks", "training"})
# def model_deploy(context: dg.AssetExecutionContext, databricks_resource: DatabricksResource, config: DatabricksModelDeploymentConfig):
#     run_id = databricks_resource.run_and_stream_notebook_logs_sdk(
#         notebook_path=NOTEBOOK_ROOT_PATH + "deployment/model_deployment/notebooks/ModelDeployment.py",
#         parameters={"env":config.env
#         }
#     )
#     context.log.info(f"Model training notebook submitted. Run ID: {run_id}")

# @dg.asset(deps=[model_training, feature_engineering_dropoff, feature_engineering_pickup, model_deploy],
#        kinds={"databricks", "training"})
# def batch_inference(context: dg.AssetExecutionContext, databricks_resource: DatabricksResource, config: DatabricksBatchInferenceConfig):
#     run_id = databricks_resource.run_and_stream_notebook_logs_sdk(
#         notebook_path=NOTEBOOK_ROOT_PATH + "deployment/batch_inference/notebooks/BatchInference",
#         parameters={"model_type": config.model_type,
#                     "input_table_name": config.input_table,
#                     "output_table_name": config.output_table},
#     )
#     context.log.info(f"Batch inference notebook submitted. Run ID: {run_id}")


# # TODO add logic to check the results of the notebook and then to decide whether it's in violation or not
# @dg.asset(deps=[batch_inference], kinds={"databricks", "inference"})
# def monitoring(context: dg.AssetExecutionContext, config: DatabricksMetricsMonitoringConfig):
#     run_id = dg.run_and_stream_notebook_logs_sdk(
#         notebook_path=NOTEBOOK_ROOT_PATH + "monitoring/notebooks/MonitoredMetricViolationCheck",
#         parameters={
#             "env": config.env,
#             "table_name_under_monitor": config.table_name_under_monitor,
#             "metric_to_monitor": config.metric_to_monitor,
#             "metric_violation_threshold": config.metric_violation_threshold,
#             "num_evaluation_windows": config.num_evaluation_windows,
#             "num_violation_windows": config.num_violation_windows
#         },
#     )
#     context.log.info(f"Monitoring notebook submitted. Run ID: {run_id}")


# @dg.multi_asset(
#     specs=[
#         dg.AssetSpec(
#             key="feature_engineering_pickup_task",
#             kinds={"databricks", "feature_engineering"}
#         ),
#         dg.AssetSpec(
#             key="feature_engineering_dropoff_task",
#             kinds={"databricks", "feature_engineering"}
#         )
#     ]
# )
# def feature_engineering_job_multi_asset(context: dg.AssetExecutionContext, databricks_resource: DatabricksResource):
#     """Multi-asset that runs both pickup and dropoff feature engineering as a single Databricks job."""

#     # Create proper Databricks SDK task objects
#     pickup_task = jobs.SubmitTask(
#         task_key="pickup_features",
#         notebook_task=jobs.NotebookTask(
#             notebook_path=NOTEBOOK_ROOT_PATH + "feature_engineering/notebooks/GenerateAndWriteFeatures",
#             base_parameters={
#                 "model_type": "RandomForest",
#                 "training_data_path": "/databricks-datasets/nyctaxi-with-zipcodes/subsampled",
#                 "timestamp_column": "tpep_pickup_datetime",
#                 "output_table_name": f"{get_env()}.databricks_mlops.trip_pickup_features",
#                 "features_transform_module": "pickup_features",
#                 "primary_keys": "zip"
#             }
#         ),
#         # serverless so ignore this
#         # new_cluster=jobs.ClusterSpec(
#         #     spark_version="13.3.x-scala2.12",
#         #     node_type_id="i3.xlarge",
#         #     num_workers=1
#         # )
#     )

#     dropoff_task = jobs.SubmitTask(
#         task_key="dropoff_features",
#         notebook_task=jobs.NotebookTask(
#             notebook_path=NOTEBOOK_ROOT_PATH + "feature_engineering/notebooks/GenerateAndWriteFeatures",
#             base_parameters={
#                 "model_type": "RandomForest",
#                 "training_data_path": "/databricks-datasets/nyctaxi-with-zipcodes/subsampled",
#                 "timestamp_column": "tpep_dropoff_datetime",
#                 "output_table_name": f"{get_env()}.databricks_mlops.trip_dropoff_features",
#                 "features_transform_module": "dropoff_features",
#                 "primary_keys": "zip"
#             }
#         ),
#         # serverless so ignore this
#         # new_cluster=jobs.ClusterSpec(
#         #     spark_version="13.3.x-scala2.12",
#         #     node_type_id="i3.xlarge",
#         #     num_workers=1
#         # )
#     )

#     client = databricks_resource.workspace_client()
#     # Submit the job using the workspace client directly
#     job_run = client.jobs.submit(
#         run_name=f"feature_engineering_job_{context.run_id}",
#         tasks=[pickup_task, dropoff_task]
#     )

#     context.log.info(f"Submitted Databricks job with run ID: {job_run.run_id}")

#     # Wait for job completion and stream logs
#     client.jobs.wait_get_run_job_terminated_or_skipped(job_run.run_id)

#     # Get final job status
#     final_run = client.jobs.get_run(job_run.run_id)

#     if final_run.state.result_state.value == "SUCCESS":
#         context.log.info("Both pickup and dropoff feature engineering tasks completed successfully")

#         # Report materialization for both assets
#         yield dg.MaterializeResult(
#             asset_key="feature_engineering_pickup_task",
#             metadata={
#                 "job_run_id": job_run.run_id,
#                 "task_key": "pickup_features",
#                 "status": "completed"
#             }
#         )

#         yield dg.MaterializeResult(
#             asset_key="feature_engineering_dropoff_task",
#             metadata={
#                 "job_run_id": job_run.run_id,
#                 "task_key": "dropoff_features",
#                 "status": "completed"
#             }
#         )
#     else:
#         raise Exception(f"Job failed with state: {final_run.state.result_state}")


# Example of using the DatabricksMultiNotebookJobComponent with databricks_config
# from hooli_ml.components.databricks_notebook_component import DatabricksMultiNotebookJobComponent

# # Option 1: Use databricks_config parameter to auto-generate from bundle
# databricks_mlops_component = DatabricksMultiNotebookJobComponent(
#     job_name_prefix="databricks_mlops_pipeline",
#     serverless=True,  # Use serverless compute
#     databricks_config="databricks_mlops/databricks_mlops/databricks.yml"
# )

# # Option 2: Explicit task configuration (current approach)
# # feature_engineering_component = DatabricksMultiNotebookJobComponent(
# #     job_name_prefix="feature_engineering_multi_job",
# #     serverless=True,
# #     tasks=[
# #         {
# #             "task_key": "pickup_features",
# #             "notebook_path": NOTEBOOK_ROOT_PATH + "feature_engineering/notebooks/GenerateAndWriteFeatures",
# #             "asset_specs": [
# #                 {
# #                     "key": "feature_engineering_pickup",
# #                     "description": "Pickup location feature engineering from taxi data",
# #                     "kinds": ["databricks", "feature_engineering"]
# #                 }
# #             ],
# #             "parameters": {
# #                 "model_type": "RandomForest",
# #                 "training_data_path": "/databricks-datasets/nyctaxi-with-zipcodes/subsampled",
# #                 "timestamp_column": "tpep_pickup_datetime",
# #                 "output_table_name": f"{get_env()}.databricks_mlops.trip_pickup_features",
# #                 "features_transform_module": "pickup_features",
# #                 "primary_keys": "zip"
# #             }
# #         },
# #         {
# #             "task_key": "dropoff_features",
# #             "notebook_path": NOTEBOOK_ROOT_PATH + "feature_engineering/notebooks/GenerateAndWriteFeatures",
# #             "asset_specs": [
# #                 {
# #                     "key": "feature_engineering_dropoff",
# #                     "description": "Dropoff location feature engineering from taxi data",
# #                     "kinds": ["databricks", "feature_engineering"]
# #                 }
# #             ],
# #             "parameters": {
# #                 "model_type": "RandomForest",
# #                 "training_data_path": "/databricks-datasets/nyctaxi-with-zipcodes/subsampled",
# #                 "timestamp_column": "tpep_dropoff_datetime",
# #                 "output_table_name": f"{get_env()}.databricks_mlops.trip_dropoff_features",
# #                 "features_transform_module": "dropoff_features",
# #                 "primary_keys": "zip"
# #             }
# #         }
# #     ]
# # )

# # Build component definitions
# component_defs = databricks_mlops_component.build_defs(None)

# monitoring_job = dg.define_asset_job(
#     name="monitoring_job",
#     selection=["monitoring"],
# )

# feature_engineering_schedule = dg.ScheduleDefinition(
#     name="feature_engineering_schedule",
#     target=["feature_engineering_pickup", "feature_engineering_pickup"],
#     cron_schedule="0 0 7 * *"
# )

# feature_engineering_schedule = dg.ScheduleDefinition(
#     name="training_and_deployment_schedule",
#     target=["model_training", "model_validation", "model_deploy"],
#     cron_schedule="0 0 9 * *"
# )

# monitoring_schedule = dg.ScheduleDefinition(
#     job=monitoring_job,
#     cron_schedule="18 * * * *",  # every 30 minutes
# )

# batch_inference_schedule = dg.ScheduleDefinition(
#     name="batch_inference_schedule",
#     target=["batch_inference",],
#     cron_schedule="0 0 11 * *"
# )


# defs = dg.Definitions(
#     assets=[
#         # Individual assets (commented out in favor of component)
#         # feature_engineering_pickup,
#         # model_training,
#         # model_validation
#         # model_validation,  # Uncomment if validation is implemented
#         # model_deploy,  # Uncomment if deployment is implemented
#         # batch_inference,  # Uncomment if batch inference is implemented
#         # monitoring,  # Uncomment if monitoring is implemented
#     ] + component_defs.assets,  # Add component-generated assets
#     schedules=[monitoring_schedule, feature_engineering_schedule, batch_inference_schedule],
#     jobs=[monitoring_job] + component_defs.jobs  # Add component-generated jobs
# )
