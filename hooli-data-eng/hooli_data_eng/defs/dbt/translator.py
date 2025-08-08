import textwrap
from typing import Any, Mapping
import dagster as dg
from dagster_dbt import (
    DagsterDbtTranslator,
    default_metadata_from_dbt_resource_props,
    DagsterDbtTranslatorSettings,
)


def get_allow_outdated_and_missing_parents_condition():
    became_missing_or_any_parents_updated = (
        dg.AutomationCondition.missing().newly_true().with_label("became missing")
        | dg.AutomationCondition.any_deps_match(
            dg.AutomationCondition.newly_updated()
            | dg.AutomationCondition.will_be_requested()
        ).with_label("any parents updated")
    )

    return (
        dg.AutomationCondition.in_latest_time_window()
        & became_missing_or_any_parents_updated.since(
            dg.AutomationCondition.newly_requested()
            | dg.AutomationCondition.newly_updated()
        )
        & ~dg.AutomationCondition.in_progress()
    ).with_label(
        "update non-partitioned asset while allowing some missing or outdated parent partitions"
    )


class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    def get_description(self, dbt_resource_props: Mapping[str, Any]) -> str:
        description = f"dbt model for: {dbt_resource_props['name']} \n \n"

        return description + textwrap.indent(
            dbt_resource_props.get("raw_code", ""), "\t"
        )

    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> dg.AssetKey:
        node_path = dbt_resource_props["path"]
        prefix = node_path.split("/")[0]

        if node_path == "models/sources.yml":
            prefix = "RAW_DATA"

        if node_path == "MARKETING/company_perf.sql":
            prefix = "ANALYTICS"

        return dg.AssetKey([prefix, dbt_resource_props["name"]])

    def get_group_name(self, dbt_resource_props: Mapping[str, Any]):
        node_path = dbt_resource_props["path"]
        prefix = node_path.split("/")[0]

        if node_path == "models/sources.yml":
            prefix = "RAW_DATA"

        if node_path == "MARKETING/company_perf.sql":
            prefix = "ANALYTICS"
        return prefix

    def get_metadata(self, dbt_resource_props: Mapping[str, Any]) -> Mapping[str, Any]:
        metadata = {"partition_expr": "order_date"}

        if dbt_resource_props["name"] == "orders_cleaned":
            metadata = {"partition_expr": "dt"}

        if dbt_resource_props["name"] == "users_cleaned":
            metadata = {"partition_expr": "created_at"}

        default_metadata = default_metadata_from_dbt_resource_props(dbt_resource_props)

        return {**default_metadata, **metadata}

    def get_automation_condition(self, dbt_resource_props: Mapping[str, Any]):
        if dbt_resource_props["name"] in [
            "company_stats",
            "locations_cleaned",
            "weekly_order_summary",
            "order_stats",
        ]:
            return get_allow_outdated_and_missing_parents_condition()

        if dbt_resource_props["name"] in ["sku_stats"]:
            return dg.AutomationCondition.on_cron("0 0 1 * *")

        if dbt_resource_props["name"] in ["company_perf"]:
            return dg.AutomationCondition.any_downstream_conditions()

    def get_owners(self, dbt_resource_props: Mapping[str, Any]):
        return (
            [
                dbt_resource_props.get["groups"]["owner"]["email"],
                f"team:{dbt_resource_props['groups']['name']}",
            ]
            if dbt_resource_props.get("groups") is not None
            else []
        )


def get_hooli_translator():
    return CustomDagsterDbtTranslator(
        settings=DagsterDbtTranslatorSettings(
            enable_asset_checks=True,
            enable_code_references=True,
        )
    )
