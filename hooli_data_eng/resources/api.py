# ---------------------------------------------------
# This file mimics how you might represent an external
# API in Dagster
# The API is a resource that is configured and used
# by the raw_data/__init__.py orders and users assets

# This demo uses the responses package to mock an API
# instead of relying on a real API

from dagster import resource, Field
import responses 
import requests
import pandas as pd
from hooli_data_eng.utils import random_data
import numpy as np
import random 

class RawDataAPI():
    def __init__(self, flaky):
        print(f"HERE! Flakiness set to: {flaky}")
        self.flaky = flaky

    @responses.activate
    def get_orders(self, datetime_to_process):
        # add lots of flakiness
        if self.flaky and random.randint(0,10) <= 4:
            raise Exception("API time out")

        responses.get(
            # fake endpoint
            "http://api.jaffleshop.co/v1/orders",

            # random order data returned, see utils.py
            json = random_data(
               extra_columns={"order_id": str, "quantity": int, "purchase_price": float, "sku": str},
               n = 10,
               filter_date=datetime_to_process
            ).to_json()
        )

        return requests.get("http://api.jaffleshop.co/v1/orders")

    @responses.activate
    def get_users(self, datetime_to_process):
        # add some of flakiness
        if self.flaky and random.randint(0,10) <= 2:
            raise Exception("API time out")

        responses.get(
            # fake endpoint
            "http://api.jaffleshop.co/v1/users",

            # random user data returned
            json = pd.DataFrame(
                {
                    "user_id": range(10),
                    "company": np.random.choice(
                        ["FoodCo", "ShopMart", "SportTime", "FamilyLtd"], size=10
                    ),
                    "is_test_user": np.random.choice([True, False], p=[0.002, 0.998], size=10),
                    "created_at": pd.to_datetime(datetime_to_process)
                }
            ).to_json()
        )

        return requests.get("http://api.jaffleshop.co/v1/users")
    

@resource(
        config_schema={"flaky": Field(config=bool, default_value=True)}
)
def data_api(context):
    flaky = context.resource_config["flaky"]
    return RawDataAPI(flaky)      