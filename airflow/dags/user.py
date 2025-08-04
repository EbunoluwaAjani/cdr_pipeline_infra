from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from randomuser import load_users_to_rds

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    dag_id='load_users_to_rds_dag',
    default_args=default_args,
    description='Load random users into RDS',
    start_date=datetime(2025, 8, 3),
    schedule_interval=None,
    catchup=False
) as dag:

    load_task = PythonOperator(
        task_id='load_users_to_rds_task',
        python_callable=load_users_to_rds
    )
load_task
