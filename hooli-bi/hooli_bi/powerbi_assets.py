from dagster_powerbi import (
    DagsterPowerBITranslator,
    build_semantic_model_refresh_asset_definition,
    load_powerbi_asset_specs,
)
from dagster_powerbi.translator import PowerBIContentData

from dagster import AssetKey, AssetSpec, EnvVar, TableColumn, TableSchema
from hooli_bi.powerbi_workspace import power_bi_workspace


class MyCustomPowerBITranslator(DagsterPowerBITranslator):
    def get_report_spec(self, data: PowerBIContentData) -> AssetSpec:
        spec = super().get_report_spec(data)
        specs_replaced = spec.replace_attributes(
            description=f"Report link: https://app.powerbi.com/groups/{EnvVar('AZURE_POWERBI_WORKSPACE_ID').get_value()}/reports/{data.properties['id']}",
            group_name="BI",
        )
        return specs_replaced.merge_attributes(tags={"core_kpis": ""})

    def get_semantic_model_spec(self, data: PowerBIContentData) -> AssetSpec:
        spec = super().get_semantic_model_spec(data)
        spec_replaced = spec.replace_attributes(
            description=f"Semantic model link: https://app.powerbi.com/groups/{EnvVar('AZURE_POWERBI_WORKSPACE_ID').get_value()}/datasets/{data.properties['id']}/details",
            group_name="BI",
            deps=[
                AssetKey(path=[dep.asset_key.path[1].upper(), dep.asset_key.path[2]])
                for dep in spec.deps
            ],
        ).merge_attributes(
            metadata={
                "dagster/column_schema": TableSchema(
                    columns=[
                        TableColumn(
                            name=col["name"],
                            type=col["dataType"],
                            tags={"PII": ""} if col["name"] == "USER_ID" else None,
                        )
                        for col in data.properties["tables"][0]["columns"]
                    ]
                )
            },
            tags={"core_kpis": ""},
        )
        return spec_replaced

    def get_dashboard_spec(self, data: PowerBIContentData) -> AssetSpec:
        spec = super().get_dashboard_spec(data)
        return spec.replace_attributes(group_name="BI")

    def get_data_source_spec(self, data: PowerBIContentData) -> AssetSpec:
        spec = super().get_data_source_spec(data)
        return spec.replace_attributes(group_name="BI")


powerbi_assets = [
    build_semantic_model_refresh_asset_definition(resource_key="power_bi", spec=spec)
    if spec.tags.get("dagster-powerbi/asset_type") == "semantic_model"
    else spec
    for spec in load_powerbi_asset_specs(
        power_bi_workspace,
        dagster_powerbi_translator=MyCustomPowerBITranslator,
        use_workspace_scan=True,
    )
]
