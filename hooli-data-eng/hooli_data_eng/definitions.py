import dagster as dg
from dagster.components import load_defs

import hooli_data_eng.defs

# ---------------------------------------------------
# Definitions

# Definitions are the collection of assets, jobs, schedules, resources, and sensors
# used with a project. Dagster Cloud deployments can contain mulitple projects.


@dg.definitions
def build_definitions():
    from hooli_data_eng.batch_enrichment.definitions import (
        defs as batch_enrichment_defs,
    )
    from hooli_data_eng.bi.definitions import defs as bi_defs
    from hooli_data_eng.snowflake_insights.definitions import (
        defs as snowflake_insights_defs,
    )

    return dg.Definitions.merge(
        load_defs(hooli_data_eng.defs),
        dg.Definitions(
            # only apply this setting once
            executor=dg.multiprocess_executor.configured({"max_concurrent": 3}),
        ),
        batch_enrichment_defs,
        bi_defs,
        snowflake_insights_defs,
    )
