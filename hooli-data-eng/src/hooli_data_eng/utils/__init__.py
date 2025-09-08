import os


def get_env():
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "data-eng-staging":
        return "PROD"
    if os.getenv("DAGSTER_IS_DEV_CLI"):
        return "LOCAL"
    # default to BRANCH so we use that in github CI
    return "BRANCH"
