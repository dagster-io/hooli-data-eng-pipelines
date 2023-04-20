locally:
	clear
	dagster dev

clean: 
	rm -rf ~/.dagster_home; mkdir ~/.dagster_home; cp dagster.yaml ~/.dagster_home/dagster.yaml

dagit: clean
	export DAGSTER_HOME="~/.dagster_home"; dagit

daemon:
	export DAGSTER_HOME="~/.dagster_home"; dagster-daemon run
	

run: dagit daemon

dagit_prod: clean 
	export DAGSTER_HOME="~/.dagster_home"; export DAGSTER_CLOUD_DEPLOYMENT_NAME="data-eng-prod"; dagit

daemon_prod: 
	export DAGSTER_HOME="~/.dagster_home"; export DAGSTER_CLOUD_DEPLOYMENT_NAME="data-eng-prod"; dagster-daemon run
	

run_prod: dagit_prod daemon_prod

dependencies:
	pip install -e ".[dev]"