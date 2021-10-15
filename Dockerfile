FROM python:3.8-slim

WORKDIR /opt/dagster/app

ADD requirements.txt requirements.txt

RUN pip install -r requirements.txt

ADD . .

RUN pip install -e .
