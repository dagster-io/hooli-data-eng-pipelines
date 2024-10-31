from dagster import AssetKey, AssetSpec, EnvVar
from dagster._core.definitions.asset_spec import replace_attributes
from dagster_powerbi import (
    load_powerbi_asset_specs,
    DagsterPowerBITranslator,
    build_semantic_model_refresh_asset_definition,
)
from dagster_powerbi.translator import PowerBIContentData
from hooli_data_eng.powerbi_workspace import power_bi_workspace


class MyCustomPowerBITranslator(DagsterPowerBITranslator):
    def get_report_spec(self, data: PowerBIContentData) -> AssetSpec:
        spec = super().get_report_spec(data)
        return replace_attributes(
            spec,
            description=f"Report link: https://app.powerbi.com/groups/{EnvVar("AZURE_POWERBI_WORKSPACE_ID").get_value()}/reports/{data.properties["id"]}",
            group_name="BI",
            tags={"core_kpis":"","dagster-powerbi/asset_type": "report"})

    def get_semantic_model_spec(self, data: PowerBIContentData) -> AssetSpec:       
        spec = super().get_semantic_model_spec(data)
        return replace_attributes(
            spec,
            description=f"Semantic model link: https://app.powerbi.com/groups/{EnvVar("AZURE_POWERBI_WORKSPACE_ID").get_value()}/datasets/{data.properties["id"]}/details",
            group_name="BI",
            deps=[AssetKey(path=[dep.asset_key.path[1].upper(), dep.asset_key.path[2]]) for dep in spec.deps],
            tags={"core_kpis":"","dagster-powerbi/asset_type": "semantic_model"})

    def get_dashboard_spec(self, data: PowerBIContentData) -> AssetSpec:
        spec = super().get_dashboard_spec(data)
        return replace_attributes(
            spec,
            group_name="BI"
        )
    
    def get_data_source_spec(self, data: PowerBIContentData) -> AssetSpec:
        spec = super().get_data_source_spec(data)
        return replace_attributes(
            spec,
            group_name="BI"
        )

powerbi_assets = [
    build_semantic_model_refresh_asset_definition(resource_key="power_bi", spec=spec)
    if spec.tags.get("dagster-powerbi/asset_type") == "semantic_model"
    else spec
    for spec in load_powerbi_asset_specs(
    power_bi_workspace, dagster_powerbi_translator=MyCustomPowerBITranslator, use_workspace_scan=True)
]