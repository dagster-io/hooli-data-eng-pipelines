# Hooli, Inc. Data Engineering

Dagster application code developed by the data engineering team at Hooli.

Most of this example is forked from [`dagster/examples/assets_dbt_python`](https://github.com/dagster-io/dagster)

A few notable changes from the quickstart example:

- Using different resources for different environments (DuckDB locally, snowflake + s3 in production)
- Using the official DuckDB IO Manager
- Sensors trigger a prediction job with the existing model everytime an analytics job has run, whereas running all assets creates a new model
- The model hyper parameters are passed as job config


Dev Notes:

- All branch deployments hit the Snowflake Database: DEMO_DB2_BRANCH
- Prod hits the Snowflake Database: DEMO_DB2
- Running with BRANCH or PROD locally is possible, but requires snowflake and AWS creds 
- These creds are stored as Kubernetes secrets on the hooli-user cluster, inside of user-cloud in us-west-2

