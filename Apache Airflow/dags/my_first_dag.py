from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable

def hello():
    y = 1 / 0
    print(y)


with DAG(
        dag_id="simple_dag",
        start_date=datetime(2024, 1, 1),
        schedule="* * * * *",
        catchup=False
) as dag:
    hello_task = PythonOperator(
        task_id="hello_task",
        python_callable=hello,
        retries=3,
        retry_delay=timedelta(seconds=10),  # optional
    )
