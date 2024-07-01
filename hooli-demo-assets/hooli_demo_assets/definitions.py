from dagster import (
   Definitions,  
)
from dagster._core.definitions.metadata import with_source_code_references
from dagster_cloud.metadata.source_code import link_to_git_if_cloud

from hooli_demo_assets.assets.sling import my_sling_assets
from hooli_demo_assets.jobs import daily_sling_job
from hooli_demo_assets.resources import sling_resource
from hooli_demo_assets.schedules import daily_sling_assets


defs = Definitions(
   assets=link_to_git_if_cloud(
       with_source_code_references([my_sling_assets])
   ),
   schedules=[daily_sling_assets],
   jobs=[daily_sling_job],
   resources={
       "sling": sling_resource
   },
)
