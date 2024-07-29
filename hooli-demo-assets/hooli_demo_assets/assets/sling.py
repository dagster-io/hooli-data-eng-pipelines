from dagster._core.definitions.tags import StorageKindTagSet
from dagster_embedded_elt.sling import (
   sling_assets,
   SlingResource,
)
from dagster_embedded_elt.sling.dagster_sling_translator import DagsterSlingTranslator

from hooli_demo_assets.resources import replication_config


class CustomSlingTranslator(DagsterSlingTranslator):
   def __init__(self, target_prefix="RAW_DATA"):
        super().__init__(target_prefix=target_prefix)
        self.replication_config = replication_config
        
   def get_group_name(self, stream_definition):
      for key, value in stream_definition['config'].items():
         if value == 'locations':
            group_name = 'RAW_DATA'
      return group_name
   
   def get_tags(self, stream_definition):
       # derive storage_kind from the target set in the replication_config
       storage_kind = self.replication_config.get("target", "DUCKDB")   
       if storage_kind.startswith("SNOWFLAKE"):
            storage_kind = "SNOWFLAKE"
       return {**StorageKindTagSet(storage_kind=storage_kind)}


@sling_assets(
   replication_config=replication_config,
   dagster_sling_translator=CustomSlingTranslator(),
)
def my_sling_assets(context, sling: SlingResource):
   yield from sling.replicate(context=context)
   for row in sling.stream_raw_logs():
       context.log.info(row)
