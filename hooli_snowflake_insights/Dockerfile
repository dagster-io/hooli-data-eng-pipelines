FROM python:3.12-slim

WORKDIR /opt/dagster/app

RUN apt-get update && apt-get install -y git 

RUN python -m pip uninstall oscrypto -y
RUN python -m pip install git+https://github.com/wbond/oscrypto.git@d5f3437ed24257895ae1edd9e503cfb352e635a8

ADD . .

RUN pip install -r requirements.txt
