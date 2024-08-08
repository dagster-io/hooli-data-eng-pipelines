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

TBD.

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
