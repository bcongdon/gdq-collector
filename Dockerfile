FROM python:3.6

RUN pip install pipenv

RUN apt-get install libpq-dev

RUN mkdir /app && cd /app

WORKDIR /app

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN pipenv install --deploy --system

COPY gdq_collector gdq_collector

CMD python -m gdq_collector
