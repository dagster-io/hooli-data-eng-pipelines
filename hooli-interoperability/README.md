# hooli_airlift

Airlift federation demo.

https://hooli.dagster.cloud/hooli-airlift/deployment/environment

- Ingestion, transformations, and reporting federated across instances:
    - `hooli-airflow-01` -> Dagster -> `hooli-airflow-02`-> 
- Ingestion and ML modeling federated across instances:
    - Dagster -> `hooli-airflow-02`

## Getting started

```bash
pip install -e ".[dev]"
```

Authentication with AWS:

```bash
aws sso login
```

Then, start the Dagster UI web server:

```bash
dagster dev
```

## MWAA

Two MWAA environments are used in this demo.

For access reference the [AWS console](https://us-west-2.console.aws.amazon.com/mwaa/home?region=us-west-2).
