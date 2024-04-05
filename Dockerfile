FROM python:3.11-slim

WORKDIR /opt/dagster/app

RUN apt-get update && apt-get install -y git gcc

RUN python -m pip install -U pip
RUN python -m pip install -U uv

ADD . .

RUN uv pip install --system -e .
