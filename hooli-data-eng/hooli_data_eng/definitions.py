import dagster as dg
from dagster.components import load_defs
import hooli_data_eng.defs
from hooli_data_eng.resources import get_resource_for_env


# ---------------------------------------------------
# Definitions

# Definitions are the collection of assets, jobs, schedules, resources, and sensors
# used with a project. Dagster Cloud deployments can contain mulitple projects.


defs = dg.Definitions.merge(
    load_defs(hooli_data_eng.defs),
    dg.Definitions(
        # only apply this setting once
        executor=dg.multiprocess_executor.configured({"max_concurrent": 3}),
        resources=get_resource_for_env(),
    ),
)
