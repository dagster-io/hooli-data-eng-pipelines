FROM dagster/hooli-base

ADD requirements.txt requirements.txt

RUN pip install -r requirements.txt

ADD . .

RUN pip install -e .
