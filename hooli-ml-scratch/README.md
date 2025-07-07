# Hooli ML Workflow

This folder contains a modular Databricks ML workflow using Delta Lake, Feature Store, MLflow Tracking/Registry, and batch inference jobs.

## Files
- `data_prep.py`: Data ingestion and cleaning, saves processed data to Delta Lake.
- `feature_engineering.py`: Feature engineering and registration in Databricks Feature Store.
- `train_model.py`: Model training and experiment tracking with MLflow.
- `register_model.py`: Registers the trained model in the MLflow Model Registry.
- `batch_inference.py`: Loads the production model and runs batch inference, saving results to Delta Lake.
- `requirements.txt`: Python dependencies for this workflow.

## Usage
Run each script in order, or orchestrate with Databricks Jobs for production workflows.
