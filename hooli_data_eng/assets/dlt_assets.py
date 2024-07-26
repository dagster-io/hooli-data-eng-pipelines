from dagster import AssetExecutionContext
from dagster_embedded_elt.dlt import DagsterDltResource, dlt_assets
from dlt_sources.github_from_openapi_pipeline.github_from_openapi import github_from_openapi_source
import dlt
from dlt_sources.filesystem_pipeline import s3_locations_data
from dlt_sources.filesystem import readers
from pathlib import Path 
import os 

#  import pipeline
dbt_project_path = Path(__file__).parent.parent.parent.joinpath("dbt_project")
DBT_PROJECT_DIR = os.fspath(dbt_project_path)
@dlt_assets(
    dlt_source=s3_locations_data(
        s3_bucket_name="hooli-demo",
        s3_prefix="embedded-elt/",),
    dlt_pipeline=dlt.pipeline(
        pipeline_name="locations_data",
        dataset_name="locations",
        destination=dlt.destinations.duckdb(os.path.join(DBT_PROJECT_DIR, "example.duckdb")), #"duckdb",
        progress="log",
    ),
    name="locations",
    group_name="dlt_testing",
)
def dagster_s3_assets(context: AssetExecutionContext, dlt: DagsterDltResource):
    yield from dlt.run(context=context)



@dlt_assets(
    dlt_source=
    readers(
        bucket_url="s3://hooli-demo/embedded-elt/", file_glob="*.csv"
    ),
    dlt_pipeline=dlt.pipeline(
        pipeline_name="locations_data_2",
        dataset_name="locations_2",
        destination=dlt.destinations.duckdb(os.path.join(DBT_PROJECT_DIR, "example.duckdb")), #"duckdb",
        progress="log",
    ),
    name="locations_2",
    group_name="dlt_testing",
)
def dagster_s3_assets_2(context: AssetExecutionContext, dlt: DagsterDltResource):
    yield from dlt.run(context=context)

@dlt_assets(
    dlt_source=github_from_openapi_source(),
    dlt_pipeline=dlt.pipeline(
        pipeline_name="github_from_openapi_spec",
        dataset_name="github_from_openapi_spec",
        destination=dlt.destinations.duckdb(os.path.join(DBT_PROJECT_DIR, "example.duckdb")), #"duckdb",
        progress="log",
    ),
    name="github_from_openapi_spec",
    group_name="github_from_openapi_spec",
)
def github_from_open_api_spec_assets(context: AssetExecutionContext, dlt: DagsterDltResource):
    yield from dlt.run(context=context)

# @dlt_assets(
#     dlt_source=voucherify_source( 
#     ),
#     dlt_pipeline=dlt.pipeline(
#         pipeline_name="voucherify_data",
#         dataset_name="voucherify",
#         destination="duckdb",
#         progress="log",
#     ),
#     name="voucherify",
#     group_name="voucherify",
# )
# def dagster_voucherify_assets(context: AssetExecutionContext, dlt: DagsterDltResource):
#     yield from dlt.run(context=context)
