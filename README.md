# Hooli, Inc. Data Engineering

This repository includes Dagster application code developed by the fictional data engineering team at Hooli.

## Getting Started

You can clone and run this example locally:

```
git clone https://github.com/dagster-io/hooli-data-eng-pipelines
pip install -e ".[dev]"
dagit
```

## Code Structure

To understand the structure, start with the file `hooli_data_eng/repository.py`. This example includes a few key Dagster concepts:

- *Assets*: are used to represent the datasets the Hooli data team manages. This example includes assets generated from dbt and Python.
- *Resources*: represent external systems. This example uses different resources for different environments (DuckDB locally, snowflake + s3 in production)
- *Jobs*: allow us to automate when our assets are updated. This example includes jobs that run on a *Schedule* and *Sensors* that trigger jobs to run when upstream data is ready.
- *Job Configuration* allows Dagster to parameterize tasks, this example includes a forecasting model with hyper parameters passed as job config.
- *Partitions and Backfills* allow Dagster to represent partitioned data with no additional code. This example includes a partitioned model stats asset (`hooli_data_eng/assets/forecasting/__init__.py`). Using partitions allows the Hooli data team to track model performance overtime, account for model drift, and run back tests for new models.


## Deploy Architecture 

This repository uses Dagster Cloud Hybrid architecture with GitHub Actions to provide CI/CD.
- The main branch is deployed to Dagster Cloud using `.github/workflows/deploy.yaml`. Each commit a new Docker image is built and pushed to our container registry. These images are deployed into an EKS cluster by our running Dagster Agent which also syncronizes changes with Dagster Cloud.

- The open PR in this repository shows how Dagster supports full integration testing with a *branch deployment*, in this case the PR is code for a second "competing" model. This change also highlights how you can test dependency changes. The action `.github/workflows/branch_deploy.yaml` creates the isolated branch deployment for each PR.
