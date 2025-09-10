from dagster import ConfigurableResource
import duckdb


class MyWarehouse(ConfigurableResource):
    path: str

    def get_raw_data(self):
        return duckdb.sql(f"SELECT * FROM '{self.path}'").df()
