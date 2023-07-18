# [Hooli, Inc. Data Engineering](https://github.com/BrenoFariasdaSilva/Dagster-Data-Engineering-Pipelines/)

<p align="center">
  <img src="https://wakatime.com/badge/github/BrenoFariasdaSilva/Dagster-Data-Engineering-Pipelines.svg" alt="wakatime" />
</p>

This repository includes Dagster application code developed by the fictional data engineering team at Hooli.

## Getting Started

You can clone and run this example locally:

```
git clone https://github.com/dagster-io/hooli-data-eng-pipelines
pip install -e ".[dev]"
dagster dev
```

## Code Structure

To understand the structure, start with the file `hooli_data_eng/definitions.py`. This example includes a few key Dagster concepts:

- *Assets*: are used to represent the datasets the Hooli data team manages. This example includes assets generated from dbt and Python.
- *Resources*: represent external systems. This example uses different resources for different environments (DuckDB locally, snowflake + s3 in production). The example also shows how to create custom resources, see `resources/api.py`.
- *Jobs*: allow us to automate when our assets are updated. This example includes jobs that run on a *Schedule* and *Sensors* that trigger jobs to run when upstream data is ready. Jobs can target assets, see `definitions.py` or they can define imperative operations, see `jobs/watch_s3.py`.
- *Job Configuration* allows Dagster to parameterize tasks, this example includes a forecasting model with hyper parameters passed as job config.
- *Partitions and Backfills* allow Dagster to represent partitioned data with no additional code. This example includes a partitioned model stats asset (`hooli_data_eng/assets/forecasting/__init__.py`). Using partitions allows the Hooli data team to track model performance overtime, account for model drift, and run back tests for new models.
- The asset `big_orders` in `hooli_data_eng/assets/forecasting/__init__.py` uses Spark. Locally, Spark is run through a local PySpark process. In production, a `resources/databricks.py` Databricks *Step Launcher* is used to dynamically create a Spark cluster for processing.
- The asset `model_nb` is an example of *Dagstermill* which lets you run Jupyter Notebooks as assets, including notebooks that should take upstream assets as inputs.
- *Sensors* are used to run jobs based on external events. See for example `hooli_data_eng/jobs/watch_s3.py`. 
- *Declarative Scheduling* is used to keep certain marketing and analytics assets up to date based on a stakeholder SLA using freshness policies and an asset reconciliation sensor. Examples include `hooli_data_eng/assets/marketing/__init__.py` and `dbt_project/models/ANALYTICS/daily_order_summary.sql`. 
- *Retries* are enabled for both runs and assets, making the pipeline robust to occassional flakiness. See `hooli_data_eng/definitions.py` for examples of retries on jobs, and `hooli_data_eng/assets/marketing/__init__.py` for an example of a more complex retry policy on an asset including backoff and jitter. Flakiness is generated in `hooli_data_eng/resources/api.py`.
- *Alerts* are enabled through Dagster Clould alert policies based on job tags. A custom alert is also specified to notify when assets with SLAs are later than expected. See `hooli_data_eng/assets/delayed_asset_alerts.py`. 

## Deployment Architecture 

This repository uses Dagster Cloud Hybrid architecture with GitHub Actions to provide CI/CD.
- The main branch is deployed to Dagster Cloud using `.github/workflows/deploy.yaml`. Each commit a new Docker image is built and pushed to our container registry. These images are deployed into an EKS cluster by our running Dagster Agent which also syncronizes changes with Dagster Cloud.

- The open PR in this repository shows how Dagster supports full integration testing with a *branch deployment*, in this case the PR is code for a second "competing" model. This change also highlights how you can test dependency changes. The action `.github/workflows/branch_deploy.yaml` creates the isolated branch deployment for each PR.


*Dev Notes in the Repo Wiki*
