# Databricks notebook source
##################################################################################
# Generate and Write Features Notebook
#
# This notebook can be used to generate and write features to a Databricks Feature Store table.
# It is configured and can be executed as the tasks in the write_feature_table_job workflow defined under
# ``my_mlops_project/resources/feature-engineering-workflow-resource.yml``
#
# Parameters:
#
# * input_table_path (required)   - Path to input data.
# * output_table_name (required)  - Fully qualified schema + Delta table name for the feature table where the features
# *                                 will be written to. Note that this will create the Feature table if it does not
# *                                 exist.
# * primary_keys (required)       - A comma separated string of primary key columns of the output feature table.
# *
# * timestamp_column (optional)   - Timestamp column of the input data. Used to limit processing based on
# *                                 date ranges. This column is used as the timestamp_key column in the feature table.
# * input_start_date (optional)   - Used to limit feature computations based on timestamp_column values.
# * input_end_date (optional)     - Used to limit feature computations based on timestamp_column values.
# *
# * features_transform_module (required) - Python module containing the feature transform logic.
##################################################################################


# List of input args needed to run this notebook as a job.
# Provide them via DB widgets or notebook arguments.
#
# A Hive-registered Delta table containing the input data.
dbutils.widgets.text(
    "input_table_path",
    "/databricks-datasets/nyctaxi-with-zipcodes/subsampled",
    label="Input Table Name",
)
# Input start date.
dbutils.widgets.text("input_start_date", "", label="Input Start Date")
# Input end date.
dbutils.widgets.text("input_end_date", "", label="Input End Date")
# Timestamp column. Will be used to filter input start/end dates.
# This column is also used as a timestamp key of the feature table.
dbutils.widgets.text(
    "timestamp_column", "tpep_pickup_datetime", label="Timestamp column"
)

# Feature table to store the computed features.
dbutils.widgets.text(
    "output_table_name",
    "dev.my_mlops_project.trip_pickup_features",
    label="Output Feature Table Name",
)

# Feature transform module name.
dbutils.widgets.text(
    "features_transform_module", "pickup_features", label="Features transform file."
)
# Primary Keys columns for the feature table;
dbutils.widgets.text(
    "primary_keys",
    "zip",
    label="Primary keys columns for the feature table, comma separated.",
)

# COMMAND ----------

import os
notebook_path =  '/Workspace/' + os.path.dirname(dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())
%cd $notebook_path
%cd ../features

# COMMAND ----------

# DBTITLE 1,Define input and output variables
input_table_path = dbutils.widgets.get("input_table_path")
output_table_name = dbutils.widgets.get("output_table_name")
input_start_date = dbutils.widgets.get("input_start_date")
input_end_date = dbutils.widgets.get("input_end_date")
ts_column = dbutils.widgets.get("timestamp_column")
features_module = dbutils.widgets.get("features_transform_module")
pk_columns = dbutils.widgets.get("primary_keys")

assert input_table_path != "", "input_table_path notebook parameter must be specified"
assert output_table_name != "", "output_table_name notebook parameter must be specified"

# Extract database name. Needs to be updated for Unity Catalog to the Schema name.
output_database = output_table_name.split(".")[1]

# COMMAND ----------

# DBTITLE 1,Create database.
spark.sql("CREATE DATABASE IF NOT EXISTS " + output_database)

# COMMAND ----------

# DBTITLE 1, Read input data.
raw_data = spark.read.format("delta").load(input_table_path)

# COMMAND ----------

# DBTITLE 1,Compute features.
# Compute the features. This is done by dynamically loading the features module.
from importlib import import_module

mod = import_module(features_module)
compute_features_fn = getattr(mod, "compute_features_fn")

features_df = compute_features_fn(
    input_df=raw_data,
    timestamp_column=ts_column,
    start_date=input_start_date,
    end_date=input_end_date,
)

# COMMAND ----------

# DBTITLE 1, Write computed features.
from databricks.feature_engineering import FeatureEngineeringClient

fe = FeatureEngineeringClient()

# Create the feature table if it does not exist first.
# Note that this is a no-op if a table with the same name and schema already exists.
fe.create_table(
    name=output_table_name,    
    primary_keys=[x.strip() for x in pk_columns.split(",")] + [ts_column],  # Include timeseries column in primary_keys
    timestamp_keys=[ts_column],
    df=features_df,
)

# Write the computed features dataframe.
fe.write_table(
    name=output_table_name,
    df=features_df,
    mode="merge",
)

# COMMAND ----------

dbutils.notebook.exit(0)