# ---------------------------------------------------
# This file mimics how you might represent an external
# API in Dagster
# The API is a resource that is configured and used
# by the raw_data/__init__.py orders and users assets

# This demo uses the responses package to mock an API
# instead of relying on a real API

import responses
import requests
import pandas as pd
import numpy as np
import random
import datetime
import time
import uuid
import dagster as dg
from typing import Optional, Any, Dict
from hooli_data_eng.resources import (
    snowflake_branch_io_manager,
    snowflake_prod_io_manager,
    duckdb_io_manager,
)


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


class RawDataAPI(dg.ConfigurableResource):
    flaky: Optional[bool] = True

    @responses.activate
    def get_orders(self, datetime_to_process):
        # add lots of flakiness
        print(f"Flakiness set to: {self.flaky} with type: {type(self.flaky)}")
        if self.flaky and random.randint(0, 10) <= 4:
            raise Exception("API time out")

        responses.get(
            # fake endpoint
            "http://api.jaffleshop.co/v1/orders",
            # random order data returned, see utils.py
            json=random_data(
                extra_columns={
                    "order_id": str,
                    "quantity": int,
                    "purchase_price": float,
                    "sku": str,
                },
                n=10,
                filter_date=datetime_to_process,
            ).to_json(),
        )

        return requests.get("http://api.jaffleshop.co/v1/orders")

    @responses.activate
    def get_users(self, datetime_to_process):
        # add some of flakiness
        if self.flaky and random.randint(0, 10) <= 2:
            raise Exception("API time out")

        responses.get(
            # fake endpoint
            "http://api.jaffleshop.co/v1/users",
            # random user data returned
            json=pd.DataFrame(
                {
                    "user_id": range(10),
                    "company": np.random.choice(
                        ["FoodCo", "ShopMart", "SportTime", "FamilyLtd"], size=10
                    ),
                    "is_test_user": np.random.choice(
                        [True, False], p=[0.002, 0.998], size=10
                    ),
                    "created_at": pd.to_datetime(datetime_to_process),
                }
            ).to_json(),
        )

        return requests.get("http://api.jaffleshop.co/v1/users")


# Resources represent external systems and, and specifically IO Managers
# tell dagster where our assets should be materialized. In dagster
# resources are separate from logical code to make it possible
# to develop locally, run tests, and run integration tests
#
# This project is designed for everything to run locally
# using the file system and DuckDB as the primary development resources
#
# PRs use a "branch" environment that mirrors production with
# staging Snowflake and S3 resources
#
# The production deployment on Dagster Cloud uses production Snowflake
# and S3 resources

# The dbt file dbt_project/config/profiles.yaml
# specifies what databases to targets, and locally will
# execute against a DuckDB

# Similar to having different dbt targets, here we create the resource
# configuration by environment

resource_def = {
    "LOCAL": {
        "io_manager": duckdb_io_manager,
        "api": RawDataAPI.configure_at_launch(),
    },
    "BRANCH": {
        "io_manager": snowflake_branch_io_manager,
        "api": RawDataAPI.configure_at_launch(),
    },
    "PROD": {
        "io_manager": snowflake_prod_io_manager,
        "api": RawDataAPI.configure_at_launch(),
    },
}
