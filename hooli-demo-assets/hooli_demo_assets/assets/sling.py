from dagster import AssetSpec
from dagster_embedded_elt.sling import build_sling_asset, SlingMode


raw_location = build_sling_asset(
    asset_spec=AssetSpec(key=["raw_location"]),
    source_stream="s3://hooli-demo/embedded-elt/",
    target_object= "RAW_DATA.LOCATION",
    mode=SlingMode.FULL_REFRESH,
    source_options={"format": "csv"},
    sling_resource_key="s3_to_snowflake_resource"
)