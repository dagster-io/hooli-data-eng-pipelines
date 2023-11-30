from dagster import (
    Definitions,
    load_assets_from_modules,
    
)

from hooli_demo_assets.assets import sling
from hooli_demo_assets.jobs import daily_sling_job
from hooli_demo_assets.resources import get_env, resource_def
from hooli_demo_assets.schedules import daily_sling_assets 


sling_assets = load_assets_from_modules([sling], key_prefix="RAW_DATA", group_name="RAW_DATA")

defs = Definitions(
    assets=[*sling_assets],
    schedules=[daily_sling_assets],
    jobs=[daily_sling_job],
    resources=resource_def[get_env()],
)