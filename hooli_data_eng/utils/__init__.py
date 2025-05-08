import datetime
import time
import os
import uuid
from typing import Any, Dict
import random
import numpy as np
import pandas as pd


def _random_times(n: int):
    """Generate some random times that generally become more frequent as time goes on."""
    time.sleep(0.5)
    start = pd.to_datetime("2022-01-01")
    end = pd.to_datetime(datetime.datetime.now())

    start_u = start.value // 10**9
    end_u = end.value // 10**9

    dist = np.random.standard_exponential(size=n) / 10

    clipped_flipped_dist = 1 - dist[dist <= 1]
    clipped_flipped_dist = clipped_flipped_dist[:-1]

    if len(clipped_flipped_dist) < n:
        clipped_flipped_dist = np.append(
            clipped_flipped_dist, clipped_flipped_dist[: n - len(clipped_flipped_dist)]
        )

    times = pd.to_datetime(
        (clipped_flipped_dist * (end_u - start_u)) + start_u, unit="s"
    )

    hours = times.round("60min").to_pydatetime()

    return hours


def random_data(
    extra_columns: Dict[str, Any], n: int, filter_date=None
) -> pd.DataFrame:
    skus = [
        "pepsi",
        "coke",
        "sprite",
        "coke zero",
        "powerade",
        "diet",
        "gingerale",
        "juice",
    ]

    # always have user_id
    data = {"user_id": np.random.randint(0, 1000, size=n)}

    for name, dtype in extra_columns.items():
        if name == "sku":
            data[name] = random.choices(skus, k=n)
        elif dtype is str:
            data[name] = [str(uuid.uuid4()) for _ in range(n)]
        elif dtype is int:
            data[name] = np.random.randint(0, 100, size=n)
        elif dtype is float:
            data[name] = 100 * np.random.random(size=n)

    data = pd.DataFrame(data)

    if filter_date:
        data["dt"] = pd.to_datetime(filter_date)
    else:
        data["dt"] = _random_times(n=n)

    return pd.DataFrame(data)


def get_env():
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME", "") == "data-eng-prod":
        return "PROD"
    if os.getenv("DAGSTER_IS_DEV_CLI"):
        return "LOCAL"
    # default to BRANCH so we use that in github CI
    return "BRANCH"
