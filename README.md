# Hooli, Inc. Data Engineering

Dagster application code developed by the data engineering team at Hooli.

Most of this example is forked from [`dagster/examples/assets_dbt_python`](https://github.com/dagster-io/dagster)

A few notable changes from the quickstart example:

- Using different resources for different environments (DuckDB locally, snowflake + s3 in production)
- Using the official DuckDB IO Manager
- Sensors trigger a prediction job with the existing model everytime an analytics job has run, whereas running all assets creates a new model
- The model hyper parameters are passed as job config
- There is a partitioned model stats asset that shows how a backfill can be launched, in this case for a simplified version of model back testing 
- The open PR shows a branch deployment with a second "competing" model that uses FB prophet. This change also highlights how you could test dependency changes.

TODOs:
- Add a Spark example
- Add a Jupyter Notebook


Dev Notes:

- All branch deployments hit the Snowflake Database: DEMO_DB2_BRANCH
- Prod hits the Snowflake Database: DEMO_DB2
- Running with BRANCH or PROD locally is possible, but requires snowflake and AWS creds 
- These creds are stored as Kubernetes secrets on the hooli-user cluster, inside of user-cloud in us-west-2
- The code executes as the hooli-demo user, defined in the main Elementl account. The resources (incl s3 buckets) live in the user cloud sub-account
