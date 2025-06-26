from dagster import Definitions

from hooli_data_eng.defs.bi.powerbi_workspace import power_bi_workspace

defs = Definitions(
    resources={"power_bi": power_bi_workspace},
)
