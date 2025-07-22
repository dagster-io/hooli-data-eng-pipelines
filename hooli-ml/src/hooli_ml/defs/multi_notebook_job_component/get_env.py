from typing import Callable
import dagster as dg
import os

@dg.template_var
def env(context):
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "gtm20":
        # PROD
        return 'prod'
    elif os.getenv("DAGSTER_IS_DEV_CLI"):
        # LOCAL
        return 'dev'
    else:
        # BRANCH
        return 'staging'