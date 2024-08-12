# Hooli, Inc. Data Engineering

This repository includes Dagster code developed by the fictional data engineering team at Hooli. Another realistic dagster code base is Dagster Lab's own data engineering repository which is publicly shared here: https://github.com/dagster-io/dagster-open-platform

## Getting Started

You can clone and run this example locally:

```
git clone https://github.com/dagster-io/hooli-data-eng-pipelines
pip install uv
make dependencies
make deps
make manifest
dagster dev
```

## Code Structure

The team at Hooli uses multiple projects to allow for different teams to take ownership of their own data products. You will find these projects in separate folders, eg `hooli_data_eng` and `hooli-demo-assets`. The team also uses Dagster to manage a large dbt project which is colocated in this repo in the `dbt_project` folder.

Each of these projects is deployed to Dagster+ resulting in a single pane of glass across teams, with RBAC enforcing who can launch runs of different assets. The deployment is managed by the `.github/workflows` file, and deploys to a Dasgter+ Hybrid Kubernetes setup. The `dagster_cloud.yaml` file is to configure the projects.

To see this in action checkout [this video](https://www.youtube.com/watch?v=qiOytuAjdbE&feature=youtu.be).

> Dev Note: to run multiple projects locally, you will want to use the `workspaces.yml` file. By default, `dagster dev` will run the `hooli_data_eng` project which accounts for the majority of the examples in this repo.

## Main Features

The majority of features are implemented in the hooli_data_eng project and include:
- partitioned assets, incl daily to weekly to unpartitioned mappings, and dynamic partitions
- dbt assets incl metadata such as column lineage
- parameterized assets
- resources that vary between dev, branch, and prod deployments
- pipes integrations with K8s and Databricks
- asset checks, incl dbt tests and freshness checks

Specifically, the project showcases a hypothetical use case where raw data is ingested from an API, transformed through dbt, and then used by marketing and ML teams. A few assets are worth highlighting: 

- `raw_data/orders` is a daily partitioned asset that uses the `api` resource to load fake data from an API into a warehouse. This load relies on an IO manager. The API resource accepts a configuration to determine if the fake data load should sometimes fail - this configuration can be over-ridden using the Dagster launchpad, eg in the case of a backfill. Speaking of backfills, this asset has a single run backfill policy meaning it is designed to update a single partition during regular runs, or multiple partitions at once during a backfill. This asset is scheduled to run daily thanks to the `refresh_analytics_model_job`.
- `cleaned/orders_cleaned` is a dbt model that sits downstream of the `raw_data/orders` asset. It shows how a dbt asset can depend on an upstream non-dbt asset. This asset also highlights how Dagster partitions can map to dbt models using dbt vars. The asset includes a variety of options that make it valuable to viewers in Dagster's asset catalog including a description, column schema and column lineage, row counts, an owner, and links to the source code. Finally, this asset shows how dbt tests can be represented as asset checks.
- `analytics/weekly_order_summary` is another dbt model. This dbt model is partitioned by week and is setup to run automatically using declarative automation. This asset showcases two key things: dagster can automatically resolve partition mappings (daily assets that roll up into weekly assets) and can handle scheduling without creating an uber dag or conflicting cron schedules.
- `order_forecast_model` is an asset that fits a model based on the data that has been transformed by dbt. This model is designed to be run sparringly (only for model retraining) and so is not scheduled, but is instead run through the Dagster+ UI. The asset accepts model configuration.
- `predicted_orders` is an asset that depends on the trained model, but should be run whenever the upstream dbt model is ready. This run sequence is accomplished using a dagster asset sensor (although declarative automation could work as an alternate approach).
- `databricks_asset` and `k8s_pod_asset` are both examples of Dagster pipes, where external processes are managed and tracked without requiring migrating the business logic into Dagster.
- `model_stats_by_month` is an example of a partitioned asset that tracks meaningful numeric metadata (in this case a model metric showing how good the trained model is behaving over time).
- `model_nb` shows how the dagstermill package can be used to schedule Jupyter notebooks, with an emphasis on using upstream assets within the body of the notebook while in production, but substituting those for temporary inputs during regular notebook execution.
- `avg_orders` and `min_order` are two fake marketing KPIs that are used to highlight the various approaches to monitoring asset freshness while using declarative automation. `avg_orders` relies on anomaly detection freshness checks and an eager automation condition while `min_orders` relies on a scheduled freshness check and is not automated (so will almost always fail its freshness check).
- `key_product_deepdive` is a fictional asset that represents some sort of dynamically created view. It is used to show how dynamic partition work and can be created from the Dagster+ UI. 

- The hooli-demo-assets project includes an example of doing elt with Sling, specifically loading data from s3 to snowflake. 

- The hooli_batch_enrichment project shows an example of a graph backed asset that uses dynamic outputs to achieve a map-reduce pattern.

## Dev notes on running the Sling example

- to run the `locations` dataset, uncomment out line 5-7 in [workspaces.yml](workspaces.yml)
- you will also need to install the packages in the "sling" extra (e.g. `pip install -e ".[dev,sling]")`)
- You'll need to obtain the credentials for AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
- then run `dagster dev` and both `hooli_demo_assets` and `hooli_data_eng` code locations will load
- NOTE: if you are running Sling locally, there is currently an error message if you already have a duckdb database set up the first time you run the Sling integration. You'll need to delete it and have the `location` asset be the the first thing you materialize.

## Deployment Architecture 

This repository uses Dagster Cloud Hybrid architecture with GitHub Actions to provide CI/CD.
- The main branch is deployed to Dagster Cloud using the workflow in `.github/workflows/`. Each commit a new Docker image is built and pushed to our container registry. These images are deployed into an EKS cluster by our running Dagster Agent which also syncronizes changes with Dagster Cloud.

- The open PR in this repository shows how Dagster supports full integration testing with a *branch deployment*, in this case the PR is code for a new dbt model.

*Additional Dev Notes in the Repo Wiki*
