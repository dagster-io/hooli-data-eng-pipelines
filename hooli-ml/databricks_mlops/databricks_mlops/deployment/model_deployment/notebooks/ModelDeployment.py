# Databricks notebook source
##################################################################################
# Helper notebook to transition the model stage. This notebook is run
# after the Train.py notebook as part of a multi-task job, in order to transition model
# to target stage after training completes.
#
# Note that we deploy the model to the stage in MLflow Model Registry equivalent to the
# environment in which the multi-task job is executed (e.g deploy the trained model to
# stage=Production if triggered in the prod environment). In a practical setting, we would
# recommend enabling the model validation step between  model training and automatically
# registering the model to the Production stage in prod.
#
# This notebook has the following parameters:
#
#  * env (required)  - String name of the current environment for model deployment, which decides the target stage.
#  * model_uri (required)  - URI of the model to deploy. Must be in the format "models:/<name>/<version-id>", as described in
#                            https://www.mlflow.org/docs/latest/model-registry.html#fetching-an-mlflow-model-from-the-model-registry
#                            This parameter is read as a task value
#                            (https://docs.databricks.com/dev-tools/databricks-utils.html),
#                            rather than as a notebook widget. That is, we assume a preceding task (the Train.py
#                            notebook) has set a task value with key "model_uri".
##################################################################################

# List of input args needed to run the notebook as a job.
# Provide them via DB widgets or notebook arguments.
#
# Name of the current environment
dbutils.widgets.dropdown("env", "None", ["None", "staging", "prod"], "Environment Name")

# COMMAND ----------

import os
import sys
notebook_path =  '/Workspace/' + os.path.dirname(dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())
%cd $notebook_path
%cd ..
sys.path.append("../..")

# COMMAND ----------

from deploy import deploy

model_uri = dbutils.jobs.taskValues.get("Train", "model_uri", debugValue="")
env = dbutils.widgets.get("env")
assert env != "None", "env notebook parameter must be specified"
assert model_uri != "", "model_uri notebook parameter must be specified"
deploy(model_uri, env)

# COMMAND ----------
print(
    f"Successfully completed model deployment for {model_uri}"
)
