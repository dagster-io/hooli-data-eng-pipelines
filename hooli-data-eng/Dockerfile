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

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=hooli-data-eng/uv.lock,target=uv.lock \
    --mount=type=bind,source=hooli-data-eng/pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copy dbt_project directory to maintain structure
COPY dbt_project/ /opt/dagster/dbt_project/

# Then, add the hooli-data-eng project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY hooli-data-eng/ /opt/dagster/app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev