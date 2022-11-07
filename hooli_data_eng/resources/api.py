from dagster import resource
import responses 
import requests
import pandas as pd
from hooli_data_eng.utils import random_data
import numpy as np

class RawDataAPI():
    def __init__(self):
        pass

    @responses.activate
    def get_orders(_):
        responses.get(
            "http://api.jaffleshop.co/v1/orders",
            json = random_data(
               extra_columns={"order_id": str, "quantity": int, "purchase_price": float, "sku": str},
               n = 1000
            ).to_json()
        )

        return requests.get("http://api.jaffleshop.co/v1/orders")

    @responses.activate
    def get_users(_):
        responses.get(
            "http://api.jaffleshop.co/v1/users",
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