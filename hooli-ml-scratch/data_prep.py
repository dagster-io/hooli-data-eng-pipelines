import os
import pandas as pd
import pyspark.sql.functions as F

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("hooli-ml-data-prep").getOrCreate()

# Create dummy data
df = pd.DataFrame({
    "id": [1, 2, 3, 4, 5],
    "col1": [10, 20, 30, 40, 50],
    "label": [0, 1, 0, 1, 0]
})
print("Created dummy data.")


# Save to CSV for demonstration (replace with Delta Lake or Spark as needed)
df.to_csv("/tmp/processed_data.csv", index=False)
print("Saved processed data to /tmp/processed_data.csv")

df = spark.read.format("delta").load("/mnt/raw/data")
df_clean = df.dropna().filter("label IS NOT NULL")
df_clean.write.format("delta").mode("overwrite").save("/mnt/processed/data")
