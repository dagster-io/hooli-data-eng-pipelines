from dagster_sling import (
    sling_assets,
    SlingResource,
)
from dagster_sling.dagster_sling_translator import DagsterSlingTranslator

from hooli_data_ingest.resources import replication_config


class CustomSlingTranslator(DagsterSlingTranslator):
    def __init__(self, target_prefix="RAW_DATA"):
        super().__init__(target_prefix=target_prefix)
        self.replication_config = replication_config

    def get_group_name(self, stream_definition):
        return "RAW_DATA"

    def get_kinds(self, stream_definition):
        storage_kind = self.replication_config.get("target", "DUCKDB")
        if storage_kind.startswith("SNOWFLAKE"):
            storage_kind = "SNOWFLAKE"
        return {"sling", storage_kind}


@sling_assets(
    replication_config=replication_config,
    dagster_sling_translator=CustomSlingTranslator(),
)
def my_sling_assets(context, sling: SlingResource):
    yield from (
        sling.replicate(context=context).fetch_column_metadata().fetch_row_count()
    )
    for row in sling.stream_raw_logs():
        context.log.info(row)
