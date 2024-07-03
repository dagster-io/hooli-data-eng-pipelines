from dagster_embedded_elt.sling import (
   sling_assets,
   SlingResource,
)
from dagster_embedded_elt.sling.dagster_sling_translator import DagsterSlingTranslator

from hooli_demo_assets.resources import replication_config


class CustomSlingTranslator(DagsterSlingTranslator):
   def __init__(self, target_prefix="RAW_DATA"):
        super().__init__(target_prefix=target_prefix)
        
   def get_group_name(self, stream_definition):
       return "RAW_DATA"


@sling_assets(
   replication_config=replication_config,
   dagster_sling_translator=CustomSlingTranslator(),
)
def my_sling_assets(context, sling: SlingResource):
   yield from sling.replicate(context=context)
   for row in sling.stream_raw_logs():
       context.log.info(row)
