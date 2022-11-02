This dbt project integrates with Dagster in a few ways:

1. The dbt profiles match to the dagster resource paradigm, allowing for local testing against DuckDB, staging against a Snowflake staging DB, and production against a Snowflake prod DB.

2. The dbt models refer to sources. These sources represent tables created by dagster. The use of sources allows Dagster to correctly infer and display the upstream asset dependencies of the dbt models. 

3. In dagster, the asset key prefix is used to represent the schema.
