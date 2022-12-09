from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.utils.dates import days_ago

with DAG(

    dag_id= 'bi-postprocessing',
    start_date=days_ago(1),
    schedule_interval=None,
    template_searchpath="/opt/airflow/dags/bi/scripts/",
    catchup=False,

) as dag:

    update_feature_collection_columns = PostgresOperator(
        task_id='update_feature_collection_columns',
        postgres_conn_id="SURFRIDERDB_WRITER_USER",
        sql='update_feature_collection_columns.sql',
        dag=dag
    )

