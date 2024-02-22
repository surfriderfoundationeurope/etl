from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.utils.dates import days_ago

doc_md_DAG = """
## BI Postprocessing

This DAG computes a postprocessing in  `bi.trash_river` and `bi.campaign_river` tables

#### How it works
- It updates mainly a column named `feature_collection` that will be queried by the cartography applications.
- It should not be manually triggered as it it automatically triggered by `bi-pipeline` DAG.
- It recomputes features on all data, not just new one

#### If it fails
- You can safely re-run as it replaces content and runs on all data.

#### Maintainers
- Charles Ollion or Clément Le Roux
"""

with DAG(

    dag_id= 'bi-postprocessing',
    start_date=days_ago(1),
    schedule_interval=None,
    catchup=False,
    doc_md=doc_md_DAG
) as dag:

    update_feature_collection_columns = PostgresOperator(
        task_id='update_feature_collection_columns',
        postgres_conn_id="SURFRIDERDB_WRITER_USER",
        sql='update_feature_collection_columns.sql',
        dag=dag
    )

