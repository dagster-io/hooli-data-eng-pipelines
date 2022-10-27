FROM python:3.8-slim

WORKDIR /opt/dagster/app

RUN apt-get update && apt-get install -y git

ADD . .

RUN pip install -e .
