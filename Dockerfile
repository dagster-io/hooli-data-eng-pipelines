FROM python:3.12-slim

WORKDIR /opt/dagster/app

RUN apt-get update && apt-get install -y git gcc

RUN apt install -y default-jre

RUN python -m pip install -U pip
# libcrypto fix oct 2023; should be able to remove sometime after that
RUN python -m pip uninstall oscrypto -y
RUN python -m pip install git+https://github.com/wbond/oscrypto.git@d5f3437ed24257895ae1edd9e503cfb352e635a8
RUN python -m pip install -U uv

ADD . .

RUN uv pip install --system -e .
