from dagster import (
   Definitions,  
)

from hooli_demo_assets.assets.sling import my_sling_assets
from hooli_demo_assets.jobs import daily_sling_job
from hooli_demo_assets.resources import sling_resource
from hooli_demo_assets.schedules import daily_sling_assets


defs = Definitions(
   assets=[my_sling_assets],
   schedules=[daily_sling_assets],
   jobs=[daily_sling_job],
   resources={
       "sling": sling_resource
   },
)
