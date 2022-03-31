import pyspark
import tempfile

from dagster import Field, StringSource, io_manager, check, IOManager
from dagster_azure.adls2 import PickledObjectADLS2IOManager


class ParquetAssetIOManager(IOManager):
    """This IOManager writes pyspark DataFrames as parquet files."""

    def __init__(self, pyspark, prefix):
        self.prefix = prefix
        self.pyspark = pyspark

    def _get_path(self, context):
        return "/".join([self.prefix, *context.asset_key.path])

    def handle_output(self, context, obj):
        # fail if output is not a pyspark DataFrame
        check.inst_param(obj, "obj", pyspark.sql.DataFrame)
        obj.write.format("parquet").mode("overwrite").save(self._get_path(context))
        context.add_output_metadata({"num_rows": obj.count()})

    def load_input(self, context) -> pyspark.sql.DataFrame:
        return self.pyspark.spark_session.read.parquet(self._get_path(context.upstream_output))


@io_manager(config_schema={"prefix": str}, required_resource_keys={"pyspark"})
def pyspark_parquet_asset_io_manager(init_context):
    return ParquetAssetIOManager(
        init_context.resources.pyspark, prefix=init_context.resource_config["prefix"]
    )
