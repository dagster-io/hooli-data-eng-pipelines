# Databricks notebook source
##################################################################################
# Model Validation Notebook
##
# This notebook uses mlflow model validation API to run mode validation after training and registering a model
# in model registry, before deploying it to the "champion" alias.
#
# It runs as part of CD and by an automated model training job -> validation -> deployment job defined under ``my_mlops_project/resources/model-workflow-resource.yml``
#
#
# Parameters:
#
# * env                                     - Name of the environment the notebook is run in (staging, or prod). Defaults to "prod".
# * `run_mode`                              - The `run_mode` defines whether model validation is enabled or not. It can be one of the three values:
#                                             * `disabled` : Do not run the model validation notebook.
#                                             * `dry_run`  : Run the model validation notebook. Ignore failed model validation rules and proceed to move
#                                                            model to the "champion" alias.
#                                             * `enabled`  : Run the model validation notebook. Move model to the "champion" alias only if all model validation
#                                                            rules are passing.
# * enable_baseline_comparison              - Whether to load the current registered "champion" model as baseline.
#                                             Baseline model is a requirement for relative change and absolute change validation thresholds.
# * validation_input                        - Validation input. Please refer to data parameter in mlflow.evaluate documentation https://mlflow.org/docs/latest/python_api/mlflow.html#mlflow.evaluate
# * model_type                              - A string describing the model type. The model type can be either "regressor" and "classifier".
#                                             Please refer to model_type parameter in mlflow.evaluate documentation https://mlflow.org/docs/latest/python_api/mlflow.html#mlflow.evaluate
# * targets                                 - The string name of a column from data that contains evaluation labels.
#                                             Please refer to targets parameter in mlflow.evaluate documentation https://mlflow.org/docs/latest/python_api/mlflow.html#mlflow.evaluate
# * custom_metrics_loader_function          - Specifies the name of the function in my_mlops_project/validation/validation.py that returns custom metrics.
# * validation_thresholds_loader_function   - Specifies the name of the function in my_mlops_project/validation/validation.py that returns model validation thresholds.
#
# For details on mlflow evaluate API, see doc https://mlflow.org/docs/latest/python_api/mlflow.html#mlflow.evaluate
# For details and examples about performing model validation, see the Model Validation documentation https://mlflow.org/docs/latest/models.html#model-validation
#
##################################################################################

# COMMAND ----------

# MAGIC %load_ext autoreload
# MAGIC %autoreload 2

# COMMAND ----------

import os
notebook_path =  '/Workspace/' + os.path.dirname(dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())
%cd $notebook_path

# COMMAND ----------

# MAGIC %pip install -r ../../requirements.txt

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

import os
notebook_path =  '/Workspace/' + os.path.dirname(dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())
%cd $notebook_path
%cd ../

# COMMAND ----------

dbutils.widgets.text(
    "experiment_name",
    "/dev-my_mlops_project-experiment",
    "Experiment Name",
)
dbutils.widgets.dropdown("run_mode", "disabled", ["disabled", "dry_run", "enabled"], "Run Mode")
dbutils.widgets.dropdown("enable_baseline_comparison", "false", ["true", "false"], "Enable Baseline Comparison")
dbutils.widgets.text("validation_input", "SELECT * FROM delta.`dbfs:/databricks-datasets/nyctaxi-with-zipcodes/subsampled`", "Validation Input")

dbutils.widgets.text("model_type", "regressor", "Model Type")
dbutils.widgets.text("targets", "fare_amount", "Targets")
dbutils.widgets.text("custom_metrics_loader_function", "custom_metrics", "Custom Metrics Loader Function")
dbutils.widgets.text("validation_thresholds_loader_function", "validation_thresholds", "Validation Thresholds Loader Function")
dbutils.widgets.text("evaluator_config_loader_function", "evaluator_config", "Evaluator Config Loader Function")
dbutils.widgets.text("model_name", "dev.my_mlops_project.my_mlops_project-model", "Full (Three-Level) Model Name")
dbutils.widgets.text("model_version", "", "Candidate Model Version")

# COMMAND ----------
run_mode = dbutils.widgets.get("run_mode").lower()
assert run_mode == "disabled" or run_mode == "dry_run" or run_mode == "enabled"

if run_mode == "disabled":
    print(
        "Model validation is in DISABLED mode. Exit model validation without blocking model deployment."
    )
    dbutils.notebook.exit(0)
dry_run = run_mode == "dry_run"

if dry_run:
    print(
        "Model validation is in DRY_RUN mode. Validation threshold validation failures will not block model deployment."
    )
else:
    print(
        "Model validation is in ENABLED mode. Validation threshold validation failures will block model deployment."
    )

# COMMAND ----------

import importlib
import mlflow
import os
import tempfile
import traceback

from mlflow.tracking.client import MlflowClient

client = MlflowClient(registry_uri="databricks-uc")
mlflow.set_registry_uri('databricks-uc')

# set experiment
experiment_name = dbutils.widgets.get("experiment_name")
mlflow.set_experiment(experiment_name)

# set model evaluation parameters that can be inferred from the job
model_uri = dbutils.jobs.taskValues.get("Train", "model_uri", debugValue="")
model_name = dbutils.jobs.taskValues.get("Train", "model_name", debugValue="")
model_version = dbutils.jobs.taskValues.get("Train", "model_version", debugValue="")

if model_uri == "":
    model_name = dbutils.widgets.get("model_name")
    model_version = dbutils.widgets.get("model_version")
    model_uri = "models:/" + model_name + "/" + model_version

baseline_model_uri = "models:/" + model_name + "@champion"

evaluators = "default"
assert model_uri != "", "model_uri notebook parameter must be specified"
assert model_name != "", "model_name notebook parameter must be specified"
assert model_version != "", "model_version notebook parameter must be specified"

# COMMAND ----------

# take input
enable_baseline_comparison = dbutils.widgets.get("enable_baseline_comparison")


enable_baseline_comparison = "false" 
print(
    "Currently baseline model comparison is not supported for models registered with feature store. Please refer to "
    "issue https://github.com/databricks/mlops-stacks/issues/70 for more details."
)

assert enable_baseline_comparison == "true" or enable_baseline_comparison == "false"
enable_baseline_comparison = enable_baseline_comparison == "true"

validation_input = dbutils.widgets.get("validation_input")
assert validation_input
data = spark.sql(validation_input)

model_type = dbutils.widgets.get("model_type")
targets = dbutils.widgets.get("targets")

assert model_type
assert targets

custom_metrics_loader_function_name = dbutils.widgets.get("custom_metrics_loader_function")
validation_thresholds_loader_function_name = dbutils.widgets.get("validation_thresholds_loader_function")
evaluator_config_loader_function_name = dbutils.widgets.get("evaluator_config_loader_function")
assert custom_metrics_loader_function_name
assert validation_thresholds_loader_function_name
assert evaluator_config_loader_function_name
custom_metrics_loader_function = getattr(
    importlib.import_module("validation"), custom_metrics_loader_function_name
)
validation_thresholds_loader_function = getattr(
    importlib.import_module("validation"), validation_thresholds_loader_function_name
)
evaluator_config_loader_function = getattr(
    importlib.import_module("validation"), evaluator_config_loader_function_name
)
custom_metrics = custom_metrics_loader_function()
validation_thresholds = validation_thresholds_loader_function()
evaluator_config = evaluator_config_loader_function()

# COMMAND ----------

# helper methods
def get_run_link(run_info):
    return "[Run](#mlflow/experiments/{0}/runs/{1})".format(
        run_info.experiment_id, run_info.run_id
    )


def get_training_run(model_name, model_version):
    version = client.get_model_version(model_name, model_version)
    return mlflow.get_run(run_id=version.run_id)


def generate_run_name(training_run):
    return None if not training_run else training_run.info.run_name + "-validation"


def generate_description(training_run):
    return (
        None
        if not training_run
        else "Model Training Details: {0}\n".format(get_run_link(training_run.info))
    )


def log_to_model_description(run, success):
    run_link = get_run_link(run.info)
    description = client.get_model_version(model_name, model_version).description
    status = "SUCCESS" if success else "FAILURE"
    if description != "":
        description += "\n\n---\n\n"
    description += "Model Validation Status: {0}\nValidation Details: {1}".format(
        status, run_link
    )
    client.update_model_version(
        name=model_name, version=model_version, description=description
    )



from datetime import timedelta, timezone
import math
import pyspark.sql.functions as F
from pyspark.sql.types import IntegerType


def rounded_unix_timestamp(dt, num_minutes=15):
    """
    Ceilings datetime dt to interval num_minutes, then returns the unix timestamp.
    """
    nsecs = dt.minute * 60 + dt.second + dt.microsecond * 1e-6
    delta = math.ceil(nsecs / (60 * num_minutes)) * (60 * num_minutes) - nsecs
    return int((dt + timedelta(seconds=delta)).replace(tzinfo=timezone.utc).timestamp())


rounded_unix_timestamp_udf = F.udf(rounded_unix_timestamp, IntegerType())


def rounded_taxi_data(taxi_data_df):
    # Round the taxi data timestamp to 15 and 30 minute intervals so we can join with the pickup and dropoff features
    # respectively.
    taxi_data_df = (
        taxi_data_df.withColumn(
            "rounded_pickup_datetime",
            F.to_timestamp(
                rounded_unix_timestamp_udf(
                    taxi_data_df["tpep_pickup_datetime"], F.lit(15)
                )
            ),
        )
        .withColumn(
            "rounded_dropoff_datetime",
            F.to_timestamp(
                rounded_unix_timestamp_udf(
                    taxi_data_df["tpep_dropoff_datetime"], F.lit(30)
                )
            ),
        )
        .drop("tpep_pickup_datetime")
        .drop("tpep_dropoff_datetime")
    )
    taxi_data_df.createOrReplaceTempView("taxi_data")
    return taxi_data_df


data = rounded_taxi_data(data)




# COMMAND ----------


# Temporary fix as FS model can't predict as a pyfunc model
# MLflow evaluate can take a lambda function instead of a model uri for a model
# but id does not work for the baseline model as it requires a model_uri (baseline comparison is set to false)

from databricks.feature_store import FeatureStoreClient

def get_fs_model(df):
    fs_client = FeatureStoreClient()
    return (
        fs_client.score_batch(model_uri, spark.createDataFrame(df))
        .select("prediction")
        .toPandas()
    )


training_run = get_training_run(model_name, model_version)

# run evaluate
with mlflow.start_run(
    run_name=generate_run_name(training_run),
    description=generate_description(training_run),
) as run, tempfile.TemporaryDirectory() as tmp_dir:
    validation_thresholds_file = os.path.join(tmp_dir, "validation_thresholds.txt")
    with open(validation_thresholds_file, "w") as f:
        if validation_thresholds:
            for metric_name in validation_thresholds:
                f.write(
                    "{0:30}  {1}\n".format(
                        metric_name, str(validation_thresholds[metric_name])
                    )
                )
    mlflow.log_artifact(validation_thresholds_file)

    try:
        eval_result = mlflow.evaluate(
            
            model=get_fs_model,
            
            data=data,
            targets=targets,
            model_type=model_type,
            evaluators=evaluators,
            validation_thresholds=validation_thresholds,
            custom_metrics=custom_metrics,
            baseline_model=None
            if not enable_baseline_comparison
            else baseline_model_uri,
            evaluator_config=evaluator_config,
        )
        metrics_file = os.path.join(tmp_dir, "metrics.txt")
        with open(metrics_file, "w") as f:
            f.write(
                "{0:30}  {1:30}  {2}\n".format("metric_name", "candidate", "baseline")
            )
            for metric in eval_result.metrics:
                candidate_metric_value = str(eval_result.metrics[metric])
                baseline_metric_value = "N/A"
                if metric in eval_result.baseline_model_metrics:
                    mlflow.log_metric(
                        "baseline_" + metric, eval_result.baseline_model_metrics[metric]
                    )
                    baseline_metric_value = str(
                        eval_result.baseline_model_metrics[metric]
                    )
                f.write(
                    "{0:30}  {1:30}  {2}\n".format(
                        metric, candidate_metric_value, baseline_metric_value
                    )
                )
        mlflow.log_artifact(metrics_file)
        log_to_model_description(run, True)
        
        # Assign "challenger" alias to indicate model version has passed validation checks
        print("Validation checks passed. Assigning 'challenger' alias to model version.")
        client.set_registered_model_alias(model_name, "challenger", model_version)
        
    except Exception as err:
        log_to_model_description(run, False)
        error_file = os.path.join(tmp_dir, "error.txt")
        with open(error_file, "w") as f:
            f.write("Validation failed : " + str(err) + "\n")
            f.write(traceback.format_exc())
        mlflow.log_artifact(error_file)
        if not dry_run:
            raise err
        else:
            print(
                "Model validation failed in DRY_RUN. It will not block model deployment."
            )
