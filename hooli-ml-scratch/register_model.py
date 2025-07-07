import mlflow

result = mlflow.register_model(
    "runs:/<RUN_ID>/model", "HooliMLModel"
)
# Optionally transition to Staging/Production using MLflow API
