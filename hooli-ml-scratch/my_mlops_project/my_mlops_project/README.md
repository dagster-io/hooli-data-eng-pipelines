# my_mlops_project
This project comes with example ML code to train, validate and deploy a regression model to predict NYC taxi fares.
If you're a data scientist just getting started with this repo for a brand new ML project, we recommend 
adapting the provided example code to your ML problem. Then making and 
testing ML code changes on Databricks or your local machine.

The "Getting Started" docs can be found at https://docs.databricks.com/dev-tools/bundles/mlops-stacks.html.

## Table of contents
* [Code structure](#code-structure): structure of this project.

* [Configure your ML pipeline](#configure-your-ml-pipeline): making and testing ML code changes on Databricks or your local machine.

* [Iterating on ML code](#iterating-on-ml-code): making and testing ML code changes on Databricks or your local machine.
* [Next steps](#next-steps)

This directory contains an ML project based on the default
[Databricks MLOps Stacks](https://github.com/databricks/mlops-stacks),
defining a production-grade ML pipeline for automated retraining and batch inference of an ML model on tabular data.

## Code structure
This project contains the following components:

| Component                  | Description                                                                                                                                                                                                                                                                                                                                             |
|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ML Code                    | Example ML project code, with unit tested Python modules and notebooks                                                                                                                                                                                                                                                                                  |
| ML Resources as Code | ML pipeline resources (training and batch inference jobs with schedules, etc) configured and deployed through [databricks CLI bundles](https://docs.databricks.com/dev-tools/cli/bundle-cli.html)                                                                                              |

contained in the following files:

```
my_mlops_project        <- Root directory. Both monorepo and polyrepo are supported.
│
├── my_mlops_project       <- Contains python code, notebooks and ML resources related to one ML project. 
│   │
│   ├── requirements.txt        <- Specifies Python dependencies for ML code (for example: model training, batch inference).
│   │
│   ├── databricks.yml          <- databricks.yml is the root bundle file for the ML project that can be loaded by databricks CLI bundles. It defines the bundle name, workspace URL and resource config component to be included.
│   │
│   ├── training                <- Training folder contains Notebook that trains and registers the model with feature store support.
│   │
│   ├── feature_engineering     <- Feature computation code (Python modules) that implements the feature transforms.
│   │                              The output of these transforms get persisted as Feature Store tables. Most development
│   │                              work happens here.
│   │
│   ├── validation              <- Optional model validation step before deploying a model.
│   │
│   ├── monitoring              <- Model monitoring, feature monitoring, etc.
│   │
│   ├── deployment              <- Deployment and Batch inference workflows
│   │   │
│   │   ├── batch_inference     <- Batch inference code that will run as part of scheduled workflow.
│   │   │
│   │   ├── model_deployment    <- As part of CD workflow, deploy the registered model by assigning it the appropriate alias.
│   │
│   │
│   ├── tests                   <- Unit tests for the ML project, including the modules under `features`.
│   │
│   ├── resources               <- ML resource (ML jobs, MLflow models) config definitions expressed as code, across dev/staging/prod/test.
│       │
│       ├── model-workflow-resource.yml                <- ML resource config definition for model training, validation, deployment workflow
│       │
│       ├── batch-inference-workflow-resource.yml      <- ML resource config definition for batch inference workflow
│       │
│       ├── feature-engineering-workflow-resource.yml  <- ML resource config definition for feature engineering workflow
│       │
│       ├── ml-artifacts-resource.yml                  <- ML resource config definition for model and experiment
│       │
│       ├── monitoring-resource.yml           <- ML resource config definition for quality monitoring workflow
```


## Configure your ML pipeline

The sample ML code consists of the following:

* Feature computation modules under `feature_engineering` folder. 
These sample module contains features logic that can be used to generate and populate tables in Feature Store.
In each module, there is `compute_features_fn` method that you need to implement. This should compute a features dataframe
(each column being a separate feature), given the input dataframe, timestamp column and time-ranges. 
The output dataframe will be persisted in a [time-series Feature Store table](https://docs.databricks.com/machine-learning/feature-store/time-series.html).
See the example modules' documentation for more information.
* Python unit tests for feature computation modules in `tests/feature_engineering` folder.
* Feature engineering notebook, `feature_engineering/notebooks/GenerateAndWriteFeatures.py`, that reads input dataframes, dynamically loads feature computation modules, executes their `compute_features_fn` method and writes the outputs to a Feature Store table (creating it if missing).
* Training notebook that [trains](https://docs.databricks.com/machine-learning/feature-store/train-models-with-feature-store.html ) a regression model by creating a training dataset using the Feature Store client.
* Model deployment and batch inference notebooks that deploy and use the trained model. 
* An automated integration test is provided (in `.github/workflows/my_mlops_project-run-tests.yml`) that executes a multi task run on Databricks involving the feature engineering and model training notebooks.

To adapt this sample code for your use case, implement your own feature module, specifying configs such as input Delta tables/dataset path(s) to use when developing
the feature engineering pipelines.
1. Implement your feature module, address TODOs in `feature_engineering/features` and create unit test in `tests/feature_engineering`
2. Update `resources/feature-engineering-workflow-resource.yml`. Fill in notebook parameters for `write_feature_table_job`.
3. Update training data path in `resources/model-workflow-resource.yml`.

We expect most of the development to take place in the `feature_engineering` folder.


## Iterating on ML code

### Deploy ML code and resources to dev workspace using Bundles

Refer to [Local development and dev workspace](./resources/README.md#local-development-and-dev-workspace)
to use databricks CLI bundles to deploy ML code together with ML resource configs to dev workspace.

This will allow you to develop locally and use databricks CLI bundles to deploy to your dev workspace to test out code and config changes.

### Develop on Databricks using Databricks Repos

#### Prerequisites
You'll need:
* Access to run commands on a cluster running Databricks Runtime ML version 11.0 or above in your dev Databricks workspace
* To set up [Databricks Repos](https://docs.databricks.com/repos/index.html): see instructions below

#### Configuring Databricks Repos
To use Repos, [set up git integration](https://docs.databricks.com/repos/repos-setup.html) in your dev workspace.

If the current project has already been pushed to a hosted Git repo, follow the
[UI workflow](https://docs.databricks.com/repos/git-operations-with-repos.html#add-a-repo-connected-to-a-remote-repo)
to clone it into your dev workspace and iterate. 

Otherwise, e.g. if iterating on ML code for a new project, follow the steps below:
* Follow the [UI workflow](https://docs.databricks.com/repos/git-operations-with-repos.html#add-a-repo-connected-to-a-remote-repo)
  for creating a repo, but uncheck the "Create repo by cloning a Git repository" checkbox.
* Install the `dbx` CLI via `pip install --upgrade dbx`
* Run `databricks configure --profile my_mlops_project-dev --token --host <your-dev-workspace-url>`, passing the URL of your dev workspace.
  This should prompt you to enter an API token
* [Create a personal access token](https://docs.databricks.com/dev-tools/auth/pat.html)
  in your dev workspace and paste it into the prompt from the previous step
* From within the root directory of the current project, use the [dbx sync](https://dbx.readthedocs.io/en/latest/guides/python/devloop/mixed/#using-dbx-sync-repo-for-local-to-repo-synchronization) tool to copy code files from your local machine into the Repo by running
  `dbx sync repo --profile my_mlops_project-dev --source . --dest-repo your-repo-name`, where `your-repo-name` should be the last segment of the full repo name (`/Repos/username/your-repo-name`)


### Develop locally

You can iterate on the feature transform modules locally in your favorite IDE before running them on Databricks.  

#### Running code on Databricks
You can iterate on ML code by running the provided `feature_engineering/notebooks/GenerateAndWriteFeatures.py` notebook on Databricks using
[Repos](https://docs.databricks.com/repos/index.html). This notebook drives execution of
the feature transforms code defined under ``features``. You can use multiple browser tabs to edit
logic in `features` and run the feature engineering pipeline in the `GenerateAndWriteFeatures.py` notebook.

#### Prerequisites
* Python 3.8+
* Install feature engineering code and test dependencies via `pip install -I -r requirements.txt` from project root directory.
* The features transform code uses PySpark and brings up a local Spark instance for testing, so [Java (version 8 and later) is required](https://spark.apache.org/docs/latest/#downloading).
* Access to UC catalog and schema
We expect a catalog to exist with the name of the deployment target by default. 
For example, if the deployment target is dev, we expect a catalog named dev to exist in the workspace. 
If you want to use different catalog names, please update the target names declared in the [databricks.yml](./databricks.yml) file.
If changing the staging, prod, or test deployment targets, you'll also need to update the workflows located in the .github/workflows directory.

For the ML training job, you must have permissions to read the input Delta table and create experiment and models. 
i.e. for each environment:
- USE_CATALOG
- USE_SCHEMA
- MODIFY
- CREATE_MODEL
- CREATE_TABLE

For the batch inference job, you must have permissions to read input Delta table and modify the output Delta table. 
i.e. for each environment
- USAGE permissions for the catalog and schema of the input and output table.
- SELECT permission for the input table.
- MODIFY permission for the output table if it pre-dates your job.

#### Run unit tests
You can run unit tests for your ML code via `pytest tests`.



## Next Steps

When you're satisfied with initial ML experimentation (e.g. validated that a model with reasonable performance can be trained on your dataset) and ready to deploy production training/inference pipelines, ask your ops team to set up CI/CD for the current ML project if they haven't already. CI/CD can be set up as part of the

MLOps Stacks initialization even if it was skipped in this case, or this project can be added to a repo setup with CI/CD already, following the directions under "Setting up CI/CD" in the repo root directory README.

To add CI/CD to this repo:
 1. Run `databricks bundle init mlops-stacks` via the Databricks CLI
 2. Select the option to only initialize `CICD_Only`
 3. Provide the root directory of this project and answer the subsequent prompts

More details can be found on the homepage [MLOps Stacks README](https://github.com/databricks/mlops-stacks/blob/main/README.md).
