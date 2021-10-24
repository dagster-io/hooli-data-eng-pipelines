from dagster import AssetKey, In, Nothing, Out, Output, op
from dagster_dbt import DbtCliOutput


@op
def preflight_comments_table(_context):
    return True


@op
def preflight_stories_table(_context):
    return True


@op(
    required_resource_keys={"dbt", "dbt_assets"},
    ins={
        "comments_table_ready": In(
            dagster_type=bool,
            asset_key=AssetKey(["snowflake", "hackernews", "comments"]),
        ),
        "stories_table_ready": In(
            dagster_type=bool,
            asset_key=AssetKey(["snowflake", "hackernews", "stories"]),
        ),
    },
    out=Out(dagster_type=DbtCliOutput),
    tags={"kind": "dbt"},
)
def hn_dbt_run(context, comments_table_ready, stories_table_ready):
    dbt_cli_output = context.resources.dbt.run()
    # here, we use a resource to determine which AssetMaterialization events to yield for
    # a given DbtCliOutput. This is done so we can swap out this implementation between modes,
    # as dbt will output to different locations depending on which profile is being used.

    # if you don't use the Dagster Asset Catalog, this can be omitted.
    for materialization in context.resources.dbt_assets.get_asset_materializations(
        dbt_cli_output
    ):
        yield materialization
    yield Output(dbt_cli_output)


@op(required_resource_keys={"dbt"}, tags={"kind": "dbt"})
def hn_dbt_test(context, _dbt_output):
    context.resources.dbt.test()
