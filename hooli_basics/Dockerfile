FROM python:3.8-slim

WORKDIR /opt/dagster/app

ADD . .

RUN python -m pip install -U uv
RUN uv pip install --system -r requirements.txt
