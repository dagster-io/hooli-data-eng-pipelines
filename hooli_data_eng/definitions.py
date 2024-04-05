from dagster import AssetKey, AssetsDefinition, Definitions, asset


def build_fivetran_asset(key: AssetKey) -> AssetsDefinition:
    @asset(key=key, compute_kind="fivetran")
    def fivetran_asset():
        pass

    return fivetran_asset


fivetran_assets = [
    build_fivetran_asset(key=AssetKey(["fivetran", "salesforce", "account"])),
]

defs = Definitions(assets=[*fivetran_assets])
