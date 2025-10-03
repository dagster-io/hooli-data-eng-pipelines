-- Initialize predictions table with minimal schema for monitoring
-- This ensures the schema and table exist before deploying the monitoring quality monitor

CREATE SCHEMA IF NOT EXISTS ${catalog_name}.databricks_mlops
COMMENT 'Schema for databricks MLOps pipeline artifacts';

CREATE TABLE IF NOT EXISTS ${catalog_name}.databricks_mlops.predictions (
  model_id STRING COMMENT 'Model version used for prediction',
  prediction DOUBLE COMMENT 'Model prediction value',
  price DOUBLE COMMENT 'Actual/label value for the prediction',
  timestamp TIMESTAMP COMMENT 'Timestamp when prediction was made'
)
USING DELTA
COMMENT 'ML model predictions table for monitoring and inference tracking';
