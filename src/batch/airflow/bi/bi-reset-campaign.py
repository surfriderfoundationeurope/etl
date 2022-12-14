from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.utils.dates import days_ago

with DAG(

    dag_id= 'bi-reset-campaign',
    start_date=days_ago(1),
    schedule_interval=None,
    catchup=False

) as dag:

    reset_campaign = PostgresOperator(
        task_id='reset_campaign',
        postgres_conn_id="SURFRIDERDB_WRITER_USER",
        sql='reset_campaign.sql',
        dag=dag
    )

    run_bi_pipeline = TriggerDagRunOperator(
        task_id='run_bi_pipeline',
        trigger_dag_id='bi-pipeline',
        wait_for_completion=True,
        dag=dag
    )
    reset_campaign >> run_bi_pipeline
