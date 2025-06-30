# hooli-etl-pipeline

Based on [Dagster etl tutorial](https://main.archive.dagster-docs.io/etl-pipeline-tutorial/add-a-resource), ported over to run in hooli duckdb locally and Snowflake in branch deployment and prod.

This Dagster project showcases:

* How to extract data from an API endpoint and load data into a data warehouse (locally into duckdb, in prod into Snowflake).
* How to transform that data within a data warehouse using dbt 
* How to use both python-defined Dagster asssets and YAML-based Dagster Components within the same project
* How to use Jinja templating within your Dagster DbtProjectComponent to switch between different environments


Some other Dagster features present:

* Partitions
* Dagster asset checks (both python Dagster asset checks and asset checks translated from dbt)
