import os


def get_kind() -> str:
    """
    Determine the storage kind based on the environment.

    Returns:
        str: The storage kind ('snowflake' or 'duckdb').
    """
    if (
        os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "data-eng-prod"
        or os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT", "") == "1"
    ):
        return "snowflake"
    return "duckdb"
