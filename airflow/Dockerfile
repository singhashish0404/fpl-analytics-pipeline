FROM apache/airflow:3.3.1

COPY airflow/requirements-airflow.txt /requirements-airflow.txt

RUN pip install --no-cache-dir -r /requirements-airflow.txt

WORKDIR /app

COPY src/ /app/src/
COPY sql/ /app/sql/