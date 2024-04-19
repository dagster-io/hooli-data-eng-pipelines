# Hooli, Inc. Data Engineering

This repository includes Dagster application code developed by the fictional data engineering team at Hooli.

## Getting Started

You can clone and run this example locally:

```
git clone https://github.com/dagster-io/hooli-data-eng-pipelines
pip install -e ".[dev]"
make deps
make manifest
dagster dev
```

## Code Structure

To understand the structure, start with the file `hooli_data_eng/definitions.py`. This example includes a few key Dagster concepts:

- *Assets*: are used to represent the datasets the Hooli data team manages. This example includes assets generated from dbt, Python, and other sources.
- *Resources*: represent external systems. This example uses different resources for different environments (DuckDB locally, snowflake + s3 in production). The example also shows how to create custom resources, see `resources/api.py`.
- *Jobs*: allow us to automate when our assets are updated. This example includes jobs that run on a *Schedule* and *Sensors* that trigger jobs to run when upstream data is ready. Jobs can target assets, see `definitions.py` or they can define imperative operations, see `jobs/watch_s3.py`.
- *Job Configuration* allows Dagster to parameterize tasks, this example includes a forecasting model with hyper parameters passed as job config.
- *Partitions and Backfills* allow Dagster to represent partitioned data with no additional code. This example shows how daily partitioned assets can automatically be scheduled daily, and how those same daily partitions can seemlessly roll up into a weekly partitioned asset.
- The asset `big_orders` in `hooli_data_eng/assets/forecasting/__init__.py` uses Spark. Locally, Spark is run through a local PySpark process. In production, a `resources/databricks.py` Databricks *Step Launcher* is used to dynamically create a Spark cluster for processing.
- The asset `model_nb` is an example of *Dagstermill* which lets you run Jupyter Notebooks as assets, including notebooks that should take upstream assets as inputs.
- *Sensors* are used to run jobs based on external events. See for example `hooli_data_eng/jobs/watch_s3.py`. 
- *Declarative Scheduling* is used to keep certain marketing and analytics assets up to date based on a stakeholder SLA using freshness policies and auto materialization policies. Examples include `hooli_data_eng/assets/marketing/__init__.py` and `dbt_project/models/ANALYTICS/weekly_order_summary.sql`. 
- *Retries* are enabled for both runs and assets, making the pipeline robust to occassional flakiness. See `hooli_data_eng/definitions.py` for examples of retries on jobs, and `hooli_data_eng/assets/marketing/__init__.py` for an example of a more complex retry policy on an asset including backoff and jitter. Flakiness is generated in `hooli_data_eng/resources/api.py`.
- *Alerts* are enabled through Dagster Clould alert policies based on job tags. A custom alert is also specified to notify when assets with SLAs are later than expected. See `hooli_data_eng/assets/delayed_asset_alerts.py`. 

## Assets spanning Multiple Code Locations

- to run the `locations` dataset, uncomment out line 5-7 in [workspaces.yml](workspaces.yml)
- you will also need to install the packages in the "sling" extra (e.g. `pip install -e ".[dev,sling]")`)
- You'll need to obtain the credentials for AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
- then run `dagster dev` and both `hooli_demo_assets` and `hooli_data_eng` code locations will load
- NOTE: if you are running Sling locally, there is currently an error message if you already have a duckdb database set up the first time you run the Sling integration. You'll need to delete it and have the `location` asset be the the first thing you materialize.

## Deployment Architecture 

This repository uses Dagster Cloud Hybrid architecture with GitHub Actions to provide CI/CD.
- The main branch is deployed to Dagster Cloud using the workflow in `.github/workflows/`. Each commit a new Docker image is built and pushed to our container registry. These images are deployed into an EKS cluster by our running Dagster Agent which also syncronizes changes with Dagster Cloud.

- The open PR in this repository shows how Dagster supports full integration testing with a *branch deployment*, in this case the PR is code for a second "competing" model. This change also highlights how you can test dependency changes. This cxapability is also implemented in the GitHub Action in this repo.

*Dev Notes in the Repo Wiki*

## Updating Python Packages

We use a combination of `requirements.in` and `setup.py` to track necessary python pacakges. To bump package versions, run `make run_docker_update` and then commit the updated `requirements.txt` files. This allows us to control when we upgrade Dagster versions, but tries to mimimize the friction involved with doing so. You will need Docker set up on your computer to run it.