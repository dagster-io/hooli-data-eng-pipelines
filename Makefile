
clean: 
	rm -rf ~/.dagster_home; mkdir ~/.dagster_home; cp dagster.yaml ~/.dagster_home/dagster.yaml

dagit: clean
	export DAGSTER_HOME="~/.dagster_home"; dagit

daemon:
	export DAGSTER_HOME="~/.dagster_home"; dagster-daemon run
	

run: dagit daemon

