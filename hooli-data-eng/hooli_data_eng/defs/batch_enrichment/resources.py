from pathlib import Path

from dagster import (
    Definitions,
)

from hooli_data_eng.defs.batch_enrichment.api import EnrichmentAPI
from hooli_data_eng.defs.batch_enrichment.warehouse import MyWarehouse

defs = Definitions(
    resources={
        "api": EnrichmentAPI(),
        # place holder for a real warehouse with required connection config
        "warehouse": MyWarehouse(
            path=str(Path(__file__).parent.joinpath("raw_data.csv"))
        ),
    },
)
