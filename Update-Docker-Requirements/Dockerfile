FROM amd64/python:3.11-buster

WORKDIR /opt/dagster/app

RUN apt-get update && apt-get install -y make

RUN python -m pip install -U uv

ENTRYPOINT make update_python_packages