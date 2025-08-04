from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.transfers.s3_to_redshift import \
    S3ToRedshiftOperator

from cdr import load_to_s3

s3_path = "s3://cdr-faker-data-dfad0cb7"
redshift_cluster_identifier = "tf-redshift-cluster"
redshift_user = "masterdb"
redshift_database = "dev_db"
redshift_table = "cdr_records"
redshift_schema = "public"


default_args = {
    "owner": "airflow",
    "start_date": datetime(2025, 7, 30),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "cdr_pipeline",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=True,
)


def build_s3_key(session=None, **context):
    execution_date = context['ds']
    return f"cdr_{execution_date}.parquet/"


get_s3_key = PythonOperator(
    task_id="get_s3_key",
    python_callable=build_s3_key,
    provide_context=True,
    do_xcom_push=True,
    dag=dag
)

etl_task = PythonOperator(
    task_id="load_to_s3",
    python_callable=load_to_s3,
    op_args=[s3_path],
    dag=dag
)

transfer_s3_to_redshift = S3ToRedshiftOperator(
    task_id="load_to_redshift",
    redshift_data_api_kwargs={
        "database": "dev_db",
        "cluster_identifier": redshift_cluster_identifier,
        "db_user": "masterdb",
        "wait_for_completion": True,
    },
    s3_bucket="cdr-faker-data-dfad0cb7",
    s3_key="{{ ti.xcom_pull(task_ids='get_s3_key') }}",
    schema="public",
    table="cdr_records",
    copy_options=[
        "FORMAT AS PARQUET"
    ],
    redshift_conn_id="redshift_default",
    aws_conn_id="aws_default",
    method='APPEND',
    do_xcom_push=False,
    dag=dag
)

etl_task >> get_s3_key >> transfer_s3_to_redshift
