from dagster_snowflake import SnowflakeIOManager
from dagster_snowflake.snowflake_io_manager import SnowflakeDbClient
from dagster_snowflake_pandas import SnowflakePandasTypeHandler
from dagster._core.storage.db_io_manager import DbTypeHandler, DbIOManager
from dagster._core.execution.context.output import OutputContext
from typing import Sequence

# NO LONGER USED IN PROJECT, BUT EXAMPLE OF CUSTOMIZING AN INTEGRATION RESOURCE


class MyDBIOManager(DbIOManager):
    def _get_table_slice(self, context, output_context: OutputContext):
        metadata = {"partition_expr": "order_date"}

        if "orders_cleaned" in output_context.asset_key.path:
            metadata = {"partition_expr": "dt"}

        if "users_cleaned" in output_context.asset_key.path:
            metadata = {"partition_expr": "created_at"}

        output_context._metadata = metadata

        return super()._get_table_slice(context=context, output_context=output_context)


class MySnowflakeIOManager(SnowflakeIOManager):
    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [SnowflakePandasTypeHandler()]

    def create_io_manager(self, context) -> MyDBIOManager:
        return MyDBIOManager(
            db_client=SnowflakeDbClient(),
            io_manager_name="SnowflakeIOManager",
            database=self.database,
            schema=self.schema_,
            type_handlers=self.type_handlers(),
            default_load_type=self.default_load_type(),
        )
