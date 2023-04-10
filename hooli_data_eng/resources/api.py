# ---------------------------------------------------
# This file mimics how you might represent an external
# API in Dagster
# The API is a resource that is configured and used
# by the raw_data/__init__.py orders and users assets

# This demo uses the responses package to mock an API
# instead of relying on a real API

from dagster import resource
import responses 
import requests
import pandas as pd
from hooli_data_eng.utils import random_data
import numpy as np
import random 

class RawDataAPI():
    def __init__(self):
        pass

    @responses.activate
    def get_orders(_, datetime_to_process):
        # add lots of flakiness
        if random.randint(0,10) <= 4:
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
    def get_users(_):
        # add some of flakiness
        if random.randint(0,10) <= 2:
            raise Exception("API time out")

        responses.get(
            # fake endpoint
            "http://api.jaffleshop.co/v1/users",

            # random user data returned
            json = pd.DataFrame(
                {
                    "user_id": range(1000),
                    "company": np.random.choice(
                        ["FoodCo", "ShopMart", "SportTime", "FamilyLtd"], size=1000
                    ),
                    "is_test_user": np.random.choice([True, False], p=[0.002, 0.998], size=1000),
                }
            ).to_json()
        )

        return requests.get("http://api.jaffleshop.co/v1/users")
    

@resource
def data_api(_):
    return RawDataAPI()      