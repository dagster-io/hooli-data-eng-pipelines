# Databricks ML Resource Configurations
[(back to project README)](../README.md)

## Table of contents
* [Intro](#intro)
* [Local development and dev workspace](#local-development-and-dev-workspace)
* [Develop and test config changes](#develop-and-test-config-changes)
* [CI/CD](#set-up-cicd)
* [Deploy initial ML resources](#deploy-initial-ml-resources)
* [Deploy config changes](#deploy-config-changes)

## Intro

### databricks CLI bundles
MLOps Stacks ML resources are configured and deployed through [databricks CLI bundles](https://docs.databricks.com/dev-tools/cli/bundle-cli.html).
The bundle setting file must be expressed in YAML format and must contain at minimum the top-level bundle mapping.

The databricks CLI bundles top level is defined by file `my_mlops_project/databricks.yml`.
During databricks CLI bundles deployment, the root config file will be loaded, validated and deployed to workspace provided by the environment together with all the included resources.

ML Resource Configurations in this directory:
 - model workflow (`my_mlops_project/resources/model-workflow-resource.yml`)
 - batch inference workflow (`my_mlops_project/resources/batch-inference-workflow-resource.yml`)
 - monitoring resource and workflow (`my_mlops_project/resources/monitoring-resource.yml`)
 - feature engineering workflow (`my_mlops_project/resources/feature-engineering-workflow-resource.yml`)
 - model definition and experiment definition (`my_mlops_project/resources/ml-artifacts-resource.yml`)


### Deployment Config & CI/CD integration
The ML resources can be deployed to databricks workspace based on the databricks CLI bundles deployment config.
Deployment configs of different deployment targets share the general ML resource configurations with added ability to specify deployment target specific values (workspace URI, model name, jobs notebook parameters, etc).
This project ships with CI/CD workflows for developing and deploying ML resource configurations based on deployment config.

For Model Registry in Unity Catalog, we expect a catalog to exist with the name of the deployment target by default. For example, if the deployment target is `dev`, we expect a catalog named `dev` to exist in the workspace. 
If you want to use different catalog names, please update the `targets` declared in the `my_mlops_project/databricks.yml` and `my_mlops_project/resources/ml-artifacts-resource.yml` files.
If changing the `staging`, `prod`, or `test` deployment targets, you'll need to update the workflows located in the `.github/workflows` directory.


| Deployment Target | Description                                                                                                                                                                                                                           | Databricks Workspace | Model Name                          | Experiment Name                                |
|-------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------|-------------------------------------|------------------------------------------------|
| dev         | The `dev` deployment target is used by ML engineers to deploy ML resources to development workspace with `dev` configs. The config is for ML project development purposes.                                                           | dev workspace        | dev-my_mlops_project-model     | /dev-my_mlops_project-experiment     |
| staging     | The `staging` deployment target is part of the CD pipeline. Latest master content will be deployed to staging workspace with `staging` config.                                                             | staging workspace    | staging-my_mlops_project-model | /staging-my_mlops_project-experiment |
| prod        | The `prod` deployment target is part of the CD pipeline. Latest release content will be deployed to prod workspace with `prod` config.                                                                      | prod workspace       | prod-my_mlops_project-model    | /prod-my_mlops_project-experiment    |
| test        | The `test` deployment target is part of the CI pipeline. For changes targeting the master branch, upon making a PR, an integration test will be triggered and ML resources deployed to the staging workspace defined under `test` deployment target. | staging workspace    | test-my_mlops_project-model    | /test-my_mlops_project-experiment    |

During ML code development, you can deploy local ML resource configurations together with ML code to the a Databricks workspace to run the training, model validation or batch inference pipelines. The deployment will use `dev` config by default.

You can open a PR (pull request) to modify ML code or the resource config against master branch.
The PR will trigger Python unit tests, followed by an integration test executed on the staging workspace, as defined under the `test` environment resource. 

Upon merging a PR to the master branch, the master branch content will be deployed to the staging workspace with `staging` environment resource configurations.

Upon merging code into the release branch, the release branch content will be deployed to prod workspace with `prod` environment resource configurations.
![ML resource config diagram](../../docs/images/mlops-stack-deploy.png)

## Local development and dev workspace

### Set up authentication

To set up the databricks CLI using a Databricks personal access token, take the following steps:

1. Follow [databricks CLI](https://docs.databricks.com/dev-tools/cli/databricks-cli.html) to download and set up the databricks CLI locally.
2. Complete the `TODO` in `my_mlops_project/databricks.yml` to add the dev workspace URI under `targets.dev.workspace.host`.
3. [Create a personal access token](https://docs.databricks.com/dev-tools/auth/pat.html)
  in your dev workspace and copy it.
4. Set an env variable `DATABRICKS_TOKEN` with your Databricks personal access token in your terminal. For example, run `export DATABRICKS_TOKEN=dapi12345` if the access token is dapi12345.
5. You can now use the databricks CLI to validate and deploy ML resource configurations to the dev workspace.

Alternatively, you can use the other approaches described in the [databricks CLI](https://docs.databricks.com/dev-tools/cli/databricks-cli.html) documentation to set up authentication. For example, using your Databricks username/password, or seting up a local profile.

### Validate and provision ML resource configurations
1. After installing the databricks CLI and creating the `DATABRICKS_TOKEN` env variable, change to the `my_mlops_project` directory.
2. Run `databricks bundle validate` to validate the Databricks resource configurations. 
3. Run `databricks bundle deploy` to provision the Databricks resource configurations to the dev workspace. The resource configurations and your ML code will be copied together to the dev workspace. The defined resources such as Databricks Workflows, MLflow Model and MLflow Experiment will be provisioned according to the config files under `my_mlops_project/resources`.
4. Go to the Databricks dev workspace, check the defined model, experiment and workflows status, and interact with the created workflows.

### Destroy ML resource configurations
After development is done, you can run `databricks bundle destroy` to destroy (remove) the defined Databricks resources in the dev workspace. Any model version with `Production` or `Staging` stage will prevent the model from being deleted. Please update the version stage to `None` or `Archived` before destroying the ML resources.
## Set up CI/CD
Please refer to [mlops-setup](../../docs/mlops-setup.md#configure-cicd) for instructions to set up CI/CD.

## Deploy initial ML resources
After completing the prerequisites, create and push a PR branch adding all files to the Git repo:
```
git checkout -b add-ml-resource-config-and-code
git add .
git commit -m "Add ML resource config and ML code"
git push upstream add-ml-resource-config-and-code
```
Open a pull request to merge the pushed branch into the `master` branch.
Upon creating this PR, the CI workflows will be triggered.
These CI workflow will run unit and integration tests of the ML code, 
in addition to validating the Databricks resources to be deployed to both staging and prod workspaces.
Once CI passes, merge the PR into the `master` branch. This will deploy an initial set of Databricks resources to the staging workspace.
resources will be deployed to the prod workspace on pushing code to the `release` branch.

Follow the next section to configure the input and output data tables for the batch inference job.

### Setting up the batch inference job
The batch inference job expects an input Delta table with a schema that your registered model accepts (out-of-the-box we provide a working example using the `nyctaxi` dataset with the schema [trip_distance, pickup_zip and dropoff_zip]). To use the batch
inference job, set up such a Delta table in both your staging and prod workspaces. For example, with the `nyctaxi` dataset, the following code can be run in a Databricks notebook to create the batch inference input table:
```
# To test the batch job the training data can be used as input

input_table_path = "/databricks-datasets/nyctaxi-with-zipcodes/subsampled"
training_df = spark.read.format("delta").load(input_table_path)

# drop unused columns
df = df.drop("tpep_pickup_datetime", "tpep_dropoff_datetime")

# target column used for monitoring, not for predictions
df = df.withColumnRenamed('fare_amount', 'price')

spark.sql("CREATE DATABASE IF NOT EXISTS my_catalog.my_schema")

def write_to_table(df, database, table):
  (df.write
   .format("delta")
   .mode("overwrite")
   .option("overwriteSchema", "true")
   .saveAsTable(f"{database}.{table}"))

# Write the DataFrame to a Delta table
write_to_table(training_df, database="my_catalog.my_schema", table="batch_input_table")
```
Following this, update the batch_inference_job base parameters in `my_mlops_project/resources/batch-inference-workflow-resource.yml` to pass
the name of the input Delta table and the name of the output Delta table to which to write batch predictions.

As the batch job will be run with the credentials of the service principal that provisioned it, make sure that the service
principal corresponding to a particular environment has permissions to read the input Delta table and modify the output Delta table in that environment's workspace. If the Delta table is in the [Unity Catalog](https://www.databricks.com/product/unity-catalog), these permissions are

* `USAGE` permissions for the catalog and schema of the input and output table.
* `SELECT` permission for the input table.
* `MODIFY` permission for the output table if it pre-dates your job.

### Setting up model validation
The model validation workflow focuses on building a plug-and-play stack component for continuous deployment (CD) of models 
in staging and prod.
Its central purpose is to evaluate a registered model and validate its quality before deploying the model to Production/Staging.

Model validation contains three components: 
* [model-workflow-resource.yml](./model-workflow-resource.yml) contains the resource config and input parameters for model validation.
* [validation.py](../validation/validation.py) defines custom metrics and validation thresholds that are referenced by the above resource config files.
* [notebooks/ModelValidation](../validation/notebooks/ModelValidation.py) contains the validation job implementation. In most cases you don't need to modify this file.

To set up and enable model validation, update [validation.py](../validation/validation.py) to return desired custom metrics and validation thresholds, then 
resolve the `TODOs` in the ModelValidation task of [model-workflow-resource.yml](./model-workflow-resource.yml).


### Setting up monitoring
The monitoring workflow focuses on building a plug-and-play stack component for monitoring the feature drifts and model drifts and retrain based on the
violation threshold defined given the ground truth labels.

Its central purpose is to track production model performances, feature distributions and comparing different versions.

Monitoring contains four components:
* [metric_violation_check_query.py](../monitoring/metric_violation_check_query.py) defines a query that checks for violation of the monitored metric.
* [notebooks/MonitoredMetricViolationCheck](../monitoring/notebooks/MonitoredMetricViolationCheck.py) acts as an entry point, executing the violation check query against the monitored inference table.
It emits a boolean value based on the query result.
* [monitoring-resource.yml](./monitoring-resource.yml) contains the resource config, inputs parameters for monitoring, and orchestrates model retraining based on monitoring. It first runs the [notebooks/MonitoredMetricViolationCheck](../monitoring/notebooks/MonitoredMetricViolationCheck.py)
entry point then decides whether to execute the model retraining workflow.

To set up and enable monitoring:
* If it is not done already, generate inference table, join it with ground truth labels, and update the table name in [monitoring-resource.yml](./monitoring-resource.yml).
* Resolve the `TODOs`  in [monitoring-resource.yml](./monitoring-resource.yml)
* Uncomment the monitoring workflow in [databricks.yml](../databricks.yml)
* OPTIONAL: Update the query in [metric_violation_check_query.py](../monitoring/metric_violation_check_query.py) to customize when the metric is considered to be in violation.

NOTE: If ground truth labels are not available, you can still set up monitoring but should disable the retraining workflow.

Retraining Constraints:
The retraining job has constraints for optimal functioning:
* Labels must be provided by the user, joined correctly for retraining history, and available on time with the retraining frequency.
* Retraining Frequency is tightly coupled with the granularity of the monitor. Users should take into account and ensure that their retraining frequency is equal to or close to the granularity of the monitor.
    * If the granularity of the monitor is 1 day and retraining frequency is 1 hour, the job will preemptively stop as there is no new data to evaluate retraining criteria
    * If the granularity of the monitor is 1 day and retraining frequency is 1 week, retraining would be stale and not be efficient

Permissions:
Permissions for monitoring are inherited from the original table's permissions.
* Users who own the monitored table or its parent catalog/schema can create, update, and view monitors.
* Users with read permissions on the monitored table can view its monitor.

Therefore, ensure that service principals are the owners or have the necessary permissions to manage the monitored table.

## Develop and test config changes

### databricks CLI bundles schema overview
To get started, open `my_mlops_project/resources/batch-inference-workflow-resource.yml`.  The file contains the ML resource definition of a batch inference job, like:

```$xslt
new_cluster: &new_cluster
  new_cluster:
    num_workers: 3
    spark_version: 15.3.x-cpu-ml-scala2.12
    node_type_id: i3.xlarge
    custom_tags:
      clusterSource: mlops-stacks_0.4

resources:
  jobs:
    batch_inference_job:
      name: ${bundle.target}-my_mlops_project-batch-inference-job
      tasks:
        - task_key: batch_inference_job
          <<: *new_cluster
          notebook_task:
            notebook_path: ../deployment/batch_inference/notebooks/BatchInference.py
            base_parameters:
              env: ${bundle.target}
              input_table_name: batch_inference_input_table_name
              ...
```

The example above defines a Databricks job with name `${bundle.target}-my_mlops_project-batch-inference-job`
that runs the notebook under `my_mlops_project/deployment/batch_inference/notebooks/BatchInference.py` to regularly apply your ML model for batch inference. 

At the start of the resource definition, we declared an anchor `new_cluster` that will be referenced and used later. For more information about anchors in yaml schema, please refer to the [yaml documentation](https://yaml.org/spec/1.2.2/#3222-anchors-and-aliases).

We specify a `batch_inference_job` under `resources/jobs` to define a databricks workflow with internal key `batch_inference_job` and job name `{bundle.target}-my_mlops_project-batch-inference-job`.
The workflow contains a single task with task key `batch_inference_job`. The task runs notebook `../deployment/batch_inference/notebooks/BatchInference.py` with provided parameters `env` and `input_table_name` passing to the notebook.
After setting up databricks CLI, you can run command `databricks bundle schema`  to learn more about databricks CLI bundles schema.

The notebook_path is the relative path starting from the resource yaml file.

### Environment config based variables
The `${bundle.target}` will be replaced by the environment config name during the bundle deployment. For example, during the deployment of a `test` environment config, the job name will be
`test-my_mlops_project-batch-inference-job`. During the deployment of the `staging` environment config, the job name will be
`staging-my_mlops_project-batch-inference-job`.


To use different values based on different environment, you can use bundle variables based on the given target, for example,
```$xslt
variables:
  batch_inference_input_table: 
    description: The table name to be used for input to the batch inference workflow.
    default: input_table

targets:
  dev:
    variables:
      batch_inference_input_table: dev_table
  test:
    variables:
      batch_inference_input_table: test_table

new_cluster: &new_cluster
  new_cluster:
    num_workers: 3
    spark_version: 15.3.x-cpu-ml-scala2.12
    node_type_id: i3.xlarge
    custom_tags:
      clusterSource: mlops-stacks_0.4

resources:
  jobs:
    batch_inference_job:
      name: ${bundle.target}-my_mlops_project-batch-inference-job
      tasks:
        - task_key: batch_inference_job
          <<: *new_cluster
          notebook_task:
            notebook_path: ../deployment/batch_inference/notebooks/BatchInference.py
            base_parameters:
              env: ${bundle.target}
              input_table_name: ${var.batch_inference_input_table}
              ...
```
The `batch_inference_job` notebook parameter `input_table_name` is using a bundle variable `batch_inference_input_table` with default value "input_table".
The variable value will be overwritten with "dev_table" for `dev` environment config and "test_table" for `test` environment config:
- during deployment with the `dev` environment config, the `input_table_name` parameter will get the value "dev_table"
- during deployment with the `staging` environment config, the `input_table_name` parameter will get the value "input_table"
- during deployment with the `prod` environment config, the `input_table_name` parameter will get the value "input_table"
- during deployment with the `test` environment config, the `input_table_name` parameter will get the value "test_table"

### Test config changes
To test out a config change, simply edit one of the fields above. For example, increase the cluster size by updating `num_workers` from 3 to 4. 

Then follow [Local development and dev workspace](#local-development-and-dev-workspace) to deploy the change to the dev workspace.
Alternatively you can open a PR. Continuous integration will then validate the updated config and deploy tests to the to staging workspace.
## Deploy config changes

### Dev workspace deployment
Please refer to [Local development and dev workspace](#local-development-and-dev-workspace).

### Test workspace deployment(CI)
After setting up CI/CD, PRs against the master branch will trigger CI workflows to run unit tests, integration test and resource validation.
The integration test will deploy MLflow model, MLflow experiment and Databricks workflow resources defined under the `test` environment resource config to the staging workspace. The integration test then triggers a run of the model workflow to verify the ML code. 

### Staging and Prod workspace deployment(CD)
After merging a PR to the master branch, continuous deployment automation will deploy the `staging` resources to the staging workspace.

When you about to cut a release, you can create and merge a PR to merge changes from master to release. Continuous deployment automation will deploy `prod` resources to the prod workspace.

[Back to project README](../README.md)
