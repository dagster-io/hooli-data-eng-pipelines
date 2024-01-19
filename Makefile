locally: manifest
	clear
	dagster dev

clean: 
	rm -rf ~/.dagster_home; mkdir ~/.dagster_home; cp dagster.yaml ~/.dagster_home/dagster.yaml

manifest:
	pip install pyopenssl --upgrade;
	pip install click --upgrade;
	pip install dbt-core dbt-duckdb dbt-snowflake; 
	dbt parse --project-dir=dbt_project --profiles-dir=dbt_project/config --target BRANCH

stateful_dev: clean manifest
	export DAGSTER_HOME="~/.dagster_home"; dagster dev

stateful_dev_prod: clean manifest
	export DAGSTER_HOME="~/.dagster_home"; export DAGSTER_CLOUD_DEPLOYMENT_NAME="data-eng-prod"; dagster dev

dependencies:
	pip install -e ".[dev]"
