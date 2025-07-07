import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from databricks.feature_store import FeatureStoreClient

fs = FeatureStoreClient()
features_df = fs.read_table("hooli_ml.features").toPandas()
X = features_df[["feature1"]]
y = features_df["label"]

with mlflow.start_run():
    model = RandomForestClassifier().fit(X, y)
    mlflow.sklearn.log_model(model, "model")
    mlflow.log_param("n_estimators", model.n_estimators)
    mlflow.log_metric("train_score", model.score(X, y))
