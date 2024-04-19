locally: manifest
	clear
	dagster dev

clean:
	rm -rf ~/.dagster_home; mkdir ~/.dagster_home; cp dagster.yaml ~/.dagster_home/dagster.yaml

update_python_packages:
	uv pip compile --upgrade --output-file=hooli_basics/requirements.txt hooli_basics/requirements.in;
	uv pip compile --upgrade --output-file=hooli_batch_enrichment/requirements.txt hooli_batch_enrichment/setup.py;
	uv pip compile --upgrade --output-file=hooli_snowflake_insights/requirements.txt hooli_snowflake_insights/requirements.in;
	uv pip compile --upgrade --output-file=hooli-demo-assets/requirements.txt hooli-demo-assets/setup.py;
	uv pip compile --upgrade --output-file=requirements.txt setup.py;

manifest:
	dbt parse --project-dir=dbt_project --target BRANCH

deps:
	dbt deps --project-dir=dbt_project

stateful_dev: clean manifest
	export DAGSTER_HOME="~/.dagster_home"; dagster dev

stateful_dev_prod: clean manifest
	export DAGSTER_HOME="~/.dagster_home"; export DAGSTER_CLOUD_DEPLOYMENT_NAME="data-eng-prod"; dagster dev

dependencies:
	uv pip install -e ".[dev]"
