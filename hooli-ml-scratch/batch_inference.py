from databricks.feature_store import FeatureStoreClient
import mlflow.pyfunc

fs = FeatureStoreClient()
features_df = fs.read_table("hooli_ml.features").toPandas()
model = mlflow.pyfunc.load_model(model_uri="models:/HooliMLModel/Production")
preds = model.predict(features_df[["feature1"]])
# Save predictions to Delta Lake
spark.createDataFrame(features_df.assign(pred=preds)).write.format("delta").mode("overwrite").save("/mnt/predictions")
