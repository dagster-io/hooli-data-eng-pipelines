# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /opt/dagster-project/app

COPY dagster /opt/dagster
COPY internal /opt/internal
