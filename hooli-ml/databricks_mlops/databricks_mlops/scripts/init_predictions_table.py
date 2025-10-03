#!/usr/bin/env python3
"""
Initialize predictions table using Databricks SQL execution API
"""
import os
import sys
import requests

def get_warehouse_id(host: str, token: str) -> str:
    """Get the first available SQL warehouse"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"{host}/api/2.0/sql/warehouses"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to get warehouses: {response.text}")

    warehouses = response.json().get("warehouses", [])
    if not warehouses:
        raise Exception("No SQL warehouses found. Please create a SQL warehouse first.")

    # Use the first available warehouse
    warehouse_id = warehouses[0]["id"]
    warehouse_name = warehouses[0].get("name", "unknown")
    print(f"Using SQL warehouse: {warehouse_name} (ID: {warehouse_id})")
    return warehouse_id


def execute_single_statement(host: str, token: str, warehouse_id: str, statement: str) -> bool:
    """Execute a single SQL statement"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"{host}/api/2.0/sql/statements"

    payload = {
        "statement": statement,
        "warehouse_id": warehouse_id,
        "wait_timeout": "30s"
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        if result.get("status", {}).get("state") == "SUCCEEDED":
            return True
        else:
            print(f"✗ SQL execution failed. Status: {result.get('status')}")
            return False
    else:
        print(f"✗ Failed to execute SQL. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def execute_sql(host: str, token: str, catalog_name: str):
    """Execute SQL to create schema and predictions table if they don't exist"""

    # Remove trailing slash from host if present
    host = host.rstrip('/')

    # Define SQL statements (must be executed separately)
    create_schema = f"CREATE SCHEMA IF NOT EXISTS {catalog_name}.databricks_mlops COMMENT 'Schema for databricks MLOps pipeline artifacts'"

    create_table = f"""CREATE TABLE IF NOT EXISTS {catalog_name}.databricks_mlops.predictions (
  model_id STRING COMMENT 'Model version used for prediction',
  prediction DOUBLE COMMENT 'Model prediction value',
  price DOUBLE COMMENT 'Actual/label value for the prediction',
  timestamp TIMESTAMP COMMENT 'Timestamp when prediction was made'
)
USING DELTA
COMMENT 'ML model predictions table for monitoring and inference tracking'"""

    # Get an available warehouse
    warehouse_id = get_warehouse_id(host, token)

    print(f"Initializing predictions table in catalog: {catalog_name}")

    # Execute schema creation
    print("1. Creating schema...")
    if not execute_single_statement(host, token, warehouse_id, create_schema):
        return 1
    print("✓ Schema created/verified")

    # Execute table creation
    print("2. Creating predictions table...")
    if not execute_single_statement(host, token, warehouse_id, create_table):
        return 1
    print("✓ Predictions table created/verified")

    print("\n✓ Successfully initialized predictions table")
    return 0

if __name__ == "__main__":
    host = os.environ.get("DATABRICKS_HOST")
    token = os.environ.get("DATABRICKS_TOKEN")
    catalog_name = sys.argv[1] if len(sys.argv) > 1 else "dev"

    if not host or not token:
        print("Error: DATABRICKS_HOST and DATABRICKS_TOKEN must be set")
        sys.exit(1)

    print(f"Using Databricks host: {host}")
    print(f"Target catalog: {catalog_name}")

    sys.exit(execute_sql(host, token, catalog_name))
