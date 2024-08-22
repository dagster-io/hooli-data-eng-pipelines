from dagster import AssetExecutionContext, AssetKey, op, job
from dagster_sdf import SdfCliResource, sdf_assets
from dagster_sdf.dagster_sdf_translator import DagsterSdfTranslator

from hooli_data_eng.workspace import workspace

class CustomDagsterSdfTranslator(DagsterSdfTranslator):
    # get_description is implemented but I didn't test it out
    # what works in 1.8.1
    # def get_asset_key(self, fqn: str) -> AssetKey:
    #     fqn_parts = fqn.split(".")
    #     # use the schema (folder) and table name as the asset key
    #     return AssetKey([fqn_parts[1], fqn_parts[2].lower()])
    # will work in 1.8.2
    def get_asset_key(self, catalog, schema, table) -> AssetKey:
        return AssetKey([schema, table.lower()])
    # get_group_name is not implemented
    # get_metadata not implemented
    # get_owners not implemented
    # get_auto_materialize_policy / get_automation_condition not implemented
    # get_tags not implemented


# did not implement tests or incremental yet
@sdf_assets(
        workspace=workspace,
        dagster_sdf_translator=CustomDagsterSdfTranslator(),
)
def my_sdf_assets(context: AssetExecutionContext, sdf: SdfCliResource):
    yield from sdf.cli(
      ["run", "--save", "info-schema"], 
      target_dir=workspace.target_dir, 
      environment=workspace.environment,
      context=context
    ).stream()

# This op will be used to run slim CI
# not really slim right now, just runs everything
@op(out={})
def sdf_slim_ci(sdf: SdfCliResource):
    sdf_command = [
        "run",
        "--save",
        "info-schema",
    ]

    yield from sdf.cli(
        args=sdf_command,
        target_dir=workspace.target_dir, 
        environment=workspace.environment,
        dagster_sdf_translator=CustomDagsterSdfTranslator(),
    ).stream()

# This job will be triggered by Pull Request and should only run new or changed dbt models
@job
def sdf_slim_ci_job():
    sdf_slim_ci()
