import dagster as dg
from hooli_data_eng.spark.resources import resource_def
from hooli_data_eng.utils import get_env

defs = dg.Definitions(
    resources=resource_def[get_env()],
)
