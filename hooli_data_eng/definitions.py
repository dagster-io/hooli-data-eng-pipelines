import warnings
from dagster._utils.warnings import BetaWarning, PreviewWarning
import dagster as dg
from dagster.components import load_defs
import hooli_data_eng.dbt.definitions as dbt_definitions
import hooli_data_eng.custom_ingest.definitions as custom_ingest_definitions
import hooli_data_eng.databricks.definitions as databricks_definitions
import hooli_data_eng.kubernetes.definitions as kubernetes_definitions
import hooli_data_eng.scikit_learn.definitions as scikit_learn_definitions
import hooli_data_eng.files.definitions as files_definitions
import hooli_data_eng.pandas.definitions as pandas_definitions
import hooli_data_eng.notebooks.definitions as notebooks_definitions
import hooli_data_eng.spark.definitions as spark_definitions
import hooli_data_eng.defs

warnings.filterwarnings("ignore", category=PreviewWarning)
warnings.filterwarnings("ignore", category=BetaWarning)

# ---------------------------------------------------
# Assets

# Dagster assets specify what outputs we care about and
# the logical code needed to create them


# ---------------------------------------------------
# Definitions

# Definitions are the collection of assets, jobs, schedules, resources, and sensors
# used with a project. Dagster Cloud deployments can contain mulitple projects.


defs = dg.Definitions.merge(
    load_defs(hooli_data_eng.defs),
    dbt_definitions.defs,
    custom_ingest_definitions.defs,
    databricks_definitions.defs,
    scikit_learn_definitions.defs,
    kubernetes_definitions.defs,
    files_definitions.defs,
    pandas_definitions.defs,
    notebooks_definitions.defs,
    spark_definitions.defs,
    dg.Definitions(
        # only apply this setting once
        executor=dg.multiprocess_executor.configured({"max_concurrent": 3}),
    ),
)
