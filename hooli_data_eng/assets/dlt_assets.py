from dagster import AssetExecutionContext
from dagster_embedded_elt.dlt import DagsterDltResource, dlt_assets
import dlt
from dlt_sources.github import github_reactions
from pathlib import Path 
import os 

#  import pipeline
dbt_project_path = Path(__file__).parent.parent.parent.joinpath("dbt_project")
DBT_PROJECT_DIR = os.fspath(dbt_project_path)
@dlt_assets(
    dlt_source=github_reactions(
        "dagster-io", "dagster", max_items=250
    ),
    dlt_pipeline=dlt.pipeline(
        pipeline_name="github_issues",
        dataset_name="github",
        destination=dlt.destinations.duckdb(os.path.join(DBT_PROJECT_DIR, "example.duckdb")), #"duckdb",
        progress="log",
    ),
    name="github",
    group_name="github",
)
def dagster_github_assets(context: AssetExecutionContext, dlt: DagsterDltResource):
    yield from dlt.run(context=context)
