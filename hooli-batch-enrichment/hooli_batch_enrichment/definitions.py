from pathlib import Path

from dagster import (
    AnchorBasedFilePathMapping,
    AssetSelection,
    define_asset_job,
    Definitions,
    ScheduleDefinition,
    with_source_code_references,
)
from hooli_batch_enrichment.api import EnrichmentAPI
from hooli_batch_enrichment.warehouse import MyWarehouse
from hooli_batch_enrichment.assets import raw_data, enriched_data
from dagster_cloud.metadata.source_code import link_code_references_to_git_if_cloud


# define a job and schedule to run the pipeline
# alternatively could use freshness policies and auto-materialization, partitions, or other ways to orient the schedule
run_assets_job = define_asset_job(
    name="run_etl_pipeline",
    selection=AssetSelection.all(),
    tags={"dagster/max_retries": "1"},
)

run_assets_30min = ScheduleDefinition(
    name="run_assets_30min", job=run_assets_job, cron_schedule="*/30 * * * *"
)

defs = Definitions(
    assets=link_code_references_to_git_if_cloud(
        with_source_code_references([raw_data, enriched_data]),
        file_path_mapping=AnchorBasedFilePathMapping(
            local_file_anchor=Path(__file__),
            file_anchor_path_in_repository="hooli_batch_enrichment/hooli_batch_enrichment/definitions.py",
        ),
    ),
    schedules=[run_assets_30min],
    jobs=[run_assets_job],
    resources={
        "api": EnrichmentAPI(),
        # place holder for a real warehouse with required connection config
        "warehouse": MyWarehouse(path="raw_data.csv"),
    },
)
