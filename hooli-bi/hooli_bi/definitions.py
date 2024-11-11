from dagster import Definitions

from hooli_bi.powerbi_assets import powerbi_assets  # noqa: TID252
from hooli_bi.powerbi_workspace import power_bi_workspace



defs = Definitions(
    assets=[*powerbi_assets],
    resources={"power_bi": power_bi_workspace},
)
