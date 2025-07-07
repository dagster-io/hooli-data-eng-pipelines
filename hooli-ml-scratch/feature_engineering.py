from databricks.feature_store import FeatureStoreClient
import pyspark.sql.functions as F
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("hooli-ml-data-prep").getOrCreate()

fs = FeatureStoreClient()
df = spark.read.format("delta").load("/mnt/processed/data")
features_df = df.withColumn("feature1", F.col("col1") * 2)
fs.create_table(
    name="hooli_ml.features",
    primary_keys=["id"],
    df=features_df,
    description="Features for Hooli ML model"
)
