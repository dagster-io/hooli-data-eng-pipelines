# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm

WORKDIR /opt/dagster/app

# Enable bytecode compilation
#ENV UV_COMPILE_BYTECODE=1
ENV UV_PROJECT_ENVIRONMENT=/usr/local

# Copy from the cache instead of linking since it's a mounted volume
#ENV UV_LINK_MODE=copy


#RUN apt-get update && apt-get install -y git gcc default-jre
RUN apt-get update && \
    apt-get install -y default-jre && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*



COPY hooli_data_eng /opt/dagster/app/
COPY pyproject.toml  /opt/dagster/app/

RUN uv pip install -e . --system