# ---------------------------------------------------
# Define a job and sensor that watch s3
# On file updates, this sensor triggers a job
# To see an example of sensors off of assets, see definitions.py

from typing import Any
from hooli_data_eng.resources.sensor_file_managers import (
    FileSystem,
    LocalFileSystem,
    s3FileSystem,
)
from dagster import job, sensor, op, RunRequest, build_resources, SkipReason, Resource
from dagster._utils import file_relative_path
import os


# This op/job combo represent an imperative task
# that runs when the sensor triggers
# To target asset updates instead, use:
# my_job = define_asset_job("predict_job",  selection=AssetSelection.keys(["FORECASTING","predicted_orders"]))


@op
def process_file(context):
    filename = context.op_config["filename"]
    context.log.info(f"Processed file {filename}")


@job
def log_file_job():
    process_file()


# Prepare resources for the sensor
def get_env():
    if os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "") == "1":
        return "BRANCH"
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "data-eng-prod":
        return "PROD"
    return "LOCAL"


# This sensor watches for updates to the file
# "customers.txt"
@sensor(job=log_file_job)
def watch_s3_sensor(context, monitor_fs: FileSystem):
    last_mtime = float(context.cursor) if context.cursor else 0
    env = get_env()
    try:
        last_updated = monitor_fs.get_mtime("customers.txt")
        if last_updated is None:
            yield SkipReason(f"customers.txt not found, using {env}")
            return
    except:
        yield SkipReason(f"customers.txt not found HERE, using {env}")
        return

    if last_updated <= last_mtime:
        yield SkipReason(
            f"customers.txt not updated since last processing, using {env}"
        )
        return

    run_key = f"customers.txt:{str(last_updated)}"
    run_config = {"ops": {"process_file": {"config": {"filename": "customers.txt"}}}}
    yield RunRequest(run_key=run_key, run_config=run_config)
    last_mtime = last_updated

    context.update_cursor(str(last_mtime))
