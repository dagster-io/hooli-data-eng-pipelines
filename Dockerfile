FROM python:3.8-slim

WORKDIR /opt/dagster/app

RUN mkdir -p /usr/share/man/man1 /usr/share/man/man2 && \
    apt-get update -yqq \
    && apt-get upgrade -yqq && \
    apt-get install -yqq openjdk-11-jdk-headless \
    openjdk-11-jre-headless && \
    java -version

ADD requirements.txt requirements.txt

RUN pip install -r requirements.txt

ADD . .

RUN pip install -e .
