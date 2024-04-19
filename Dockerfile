FROM python:3.11-slim

WORKDIR /opt/dagster/app

RUN apt-get update && apt-get install -y git gcc

RUN apt install -y default-jre

RUN python -m pip install -U uv

ADD . .

RUN uv pip sync requirements.txt --system
