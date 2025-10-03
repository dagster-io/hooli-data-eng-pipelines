#!/usr/bin/env python3
"""
Initialize predictions table using Databricks SQL execution API
"""
import os
import sys
import time
import requests

def execute_sql(host: str, token: str, catalog_name: str):
    """Execute SQL to create schema and predictions table if they don't exist"""

    # Remove trailing slash from host if present
    host = host.rstrip('/')

    sql_statements = f"""
CREATE SCHEMA IF NOT EXISTS {catalog_name}.databricks_mlops
COMMENT 'Schema for databricks MLOps pipeline artifacts';

CREATE TABLE IF NOT EXISTS {catalog_name}.databricks_mlops.predictions (
  model_id STRING COMMENT 'Model version used for prediction',
  prediction DOUBLE COMMENT 'Model prediction value',
  price DOUBLE COMMENT 'Actual/label value for the prediction',
  timestamp TIMESTAMP COMMENT 'Timestamp when prediction was made'
)
USING DELTA
COMMENT 'ML model predictions table for monitoring and inference tracking';
"""

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Use SQL Statement Execution API
    # https://docs.databricks.com/api/workspace/statementexecution/executestatement
    url = f"{host}/api/2.0/sql/statements"

    payload = {
        "statement": sql_statements,
        "warehouse_id": None,  # Uses the default warehouse
        "wait_timeout": "30s"
    }

    print(f"Executing SQL to initialize predictions table in catalog: {catalog_name}")
    print(f"SQL:\n{sql_statements}")

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        if result.get("status", {}).get("state") == "SUCCEEDED":
            print("✓ Successfully initialized predictions table")
            return 0
        else:
            print(f"SQL execution did not succeed. Status: {result.get('status')}")
            return 1
    else:
        print(f"✗ Failed to execute SQL. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return 1

if __name__ == "__main__":
    host = os.environ.get("DATABRICKS_HOST")
    token = os.environ.get("DATABRICKS_TOKEN")
    catalog_name = sys.argv[1] if len(sys.argv) > 1 else "dev"

    if not host or not token:
        print("Error: DATABRICKS_HOST and DATABRICKS_TOKEN must be set")
        sys.exit(1)

    sys.exit(execute_sql(host, token, catalog_name))
