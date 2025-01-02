locally: manifest
	clear
	dagster dev

clean:
	rm -rf ~/.dagster_home; mkdir ~/.dagster_home; cp dagster.yaml ~/.dagster_home/dagster.yaml

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

update_packages:
	uv lock --upgrade;
	uv lock --upgrade --directory hooli_basics;
	uv lock --upgrade --directory hooli_batch_enrichment;
	uv lock --upgrade --directory hooli_snowflake_insights;
	uv lock --upgrade --directory hooli-data-ingest;
	uv lock --upgrade --directory hooli-bi;

ruff:
	-ruff check --fix .
	ruff format .

# ensure that DAGSTER_GIT_REPO_DIR is set to the path of the dagster repo
# see https://www.notion.so/dagster/Local-Dev-Setup-e58aba352f704dcc88a8dc44cb1ce7fc for more details
# ensure your virtual environment is activated here
install_from_dagster_clone:
	source .venv/bin/activate; uv pip install pip; cd ${DAGSTER_GIT_REPO_DIR} && python scripts/install_dev_python_modules.py; cd -; 