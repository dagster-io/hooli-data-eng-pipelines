FROM python:3.12-slim

WORKDIR /opt/dagster/app

ADD . .

RUN python -m pip install -U uv
RUN uv pip install --system -e .