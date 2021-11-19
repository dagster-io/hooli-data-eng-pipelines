FROM dagster/hooli-base

WORKDIR /opt/dagster/app

RUN apt-get update && apt-get install -y git

ADD requirements.txt requirements.txt

RUN pip install -r requirements.txt

ADD . .

RUN pip install -e .
