# Updating ML code in production

[(back to main README)](../README.md)

**NOTE**: This page assumes that your MLOps team has already configured CI/CD and deployed initial
ML resources, per the [MLOps setup guide](mlops-setup.md).

## Table of contents
* [Opening a pull request](#opening-a-pull-request)
* [Viewing test status and debug logs](#viewing-test-status-and-debug-logs)
* [Merging your pull request](#merging-your-pull-request)
* [Next steps](#next-steps)

## Opening a pull request

To push your updated ML code to production, [open a pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request
) against the remote Git repo containing the current project.

**NOTE**: the default tests provided in this repo require that you use a pull
request branch on the Git repo for the current project, rather than opening a pull request from a fork
of the Git repo. Support for running tests against pull requests from repo forks
is planned for the future.

## Viewing test status and debug logs
Opening a pull request will trigger a[workflow](../.github/workflows/my_mlops_project-run-tests.yml) 
that runs unit and integration tests for the model training (and feature engineering if added) pipeline on Databricks against a test dataset.
You can view test status and debug logs from the pull request UI, and push new commits to your pull request branch
to address any test failures.

The integration test runs the feature engineering and model training notebooks as a multi-task Databricks Job in the staging workspace.
It reads input data, performs feature transforms, and writes outputs to Feature Store tables in the staging workspace. 
The model training notebook uses these Feature Store tables as inputs to train, validate and register a new model version in 
UC
. 
The fitted model along with its metrics and params will also be logged to an MLflow run. 
To debug failed integration test runs, click into the Databricks job run
URL printed in the test logs. The executed notebook of the job run will contain a link to the MLflow model training run, which you can use with the Experiments page in the workspace
to view training metrics or fetch and debug the model as needed.

## Merging your pull request
Once tests pass on your pull request, get your pull request reviewed and approved by a teammate,
and then merge it into the upstream repo.

## Next Steps
After merging your pull request, subsequent runs of the model training and batch inference
jobs in staging and production will automatically use your updated ML code.

You can track the state of the ML pipelines for the current project from the MLflow registered model UI. 

Links:
* [Staging model in UC](https://your-staging-workspace.cloud.databricks.com/explore/data/models/staging/my_mlops_project/my_mlops_project-model)
* [Prod model in UC](https://dbc-07902917-6487.cloud.databricks.com/explore/data/models/prod/my_mlops_project/my_mlops_project-model)
. 


In both the staging and prod workspaces, the MLflow registered model contains links to:
* The model versions produced through automated retraining
* The Git repository containing the ML code run in the training and inference pipelines
 * The recurring Feature Store jobs that computes and writes features to Feature Store tables. 
* The recurring training job that produces new model versions using the latest ML code and data
* The model deployment CD workflow that takes model versions produced by the training job and deploys them for inference
* The recurring batch inference job that uses the currently-deployed model version to score a dataset
