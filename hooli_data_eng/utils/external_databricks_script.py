####
# This reprsents an "external" script that is mostly independent of dagster
# that dagster will orchestrate via pipes
# This script must be uploaded to Databricks manually (or via some other process)
# `dagster_pipes` must be available in the databricks python environment

from dagster_pipes import PipesDbfsContextLoader, PipesDbfsMessageWriter, PipesContext, open_dagster_pipes
import random 

with open_dagster_pipes(context_loader=PipesDbfsContextLoader(), message_writer=PipesDbfsMessageWriter()) as context:
    
    sample_rate = context.get_extra("sample_rate")

    # Stream log message back to Dagster
    context.log.info(f"Using sample rate: {sample_rate}")

    # ... your code that computes and persists the asset


    # Stream asset materialization metadata and data version back to Dagster.
    # This should be called after you've computed and stored the asset value. We
    # omit the asset key here because there is only one asset in scope, but for
    # multi-assets you can pass an `asset_key` parameter.
    context.report_asset_materialization(
        metadata={"some_spark_metric": random.choice(["scranton", "new york", "tallahassee"])},
    )