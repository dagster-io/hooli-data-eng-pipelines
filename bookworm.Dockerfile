# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm

WORKDIR /opt/dagster-project/app


COPY dagster /opt/dagster-project/dagster
COPY internal /opt/dagster-project/internal
