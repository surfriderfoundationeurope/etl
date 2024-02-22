from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.utils.dates import days_ago

doc_md_DAG = """
## BI Pipeline

This DAG triggers a series of processing named BI (Business Intelligence) which compute various metrics
related to the campaigns, trash, and users. In particular, it links the campaigns to a referential of rivers.

**VERY IMPORTANT: Always run `etl_batch_trigger_all` before running this DAG !**

#### How it works
- It selects campaigns from `campaign.campaign` where `has_been_computed` is `null`
- It uses campaign, trajectory points, trash, rivers information.
- It fills information in the `bi` tables.

When finished, it automatically starts the `bi-postprocessing` DAG.

#### If it fails
- It only writes data in the database if it works until the end (besides temporary data)
- You can safely rerun it or run it twice
- Try to see which node fails and see error in logs

#### Maintainers
- Charles Ollion or Clément Le Roux
"""

with DAG(

    dag_id="bi-pipeline",
    start_date=days_ago(1),
    schedule_interval=None,
    catchup=False,
    doc_md=doc_md_DAG
) as dag:

    get_new_campaign_ids = PostgresOperator(
        task_id='get_new_campaign_ids',
        postgres_conn_id="SURFRIDERDB_WRITER_USER",
        sql='get_new_campaign_ids.sql',
        dag=dag
    )

    copy_campaign_table = PostgresOperator(
        task_id='copy_campaign_table',
        postgres_conn_id="SURFRIDERDB_WRITER_USER",
        sql='copy_campaign_table.sql',
        dag=dag
    )

    copy_trash_table = PostgresOperator(
        task_id='copy_trash_table',
        postgres_conn_id="SURFRIDERDB_WRITER_USER",
        sql='copy_trash_table.sql',
        dag=dag
    )

    copy_trajectory_point_table = PostgresOperator(
        task_id='copy_trajectory_point_table',
        postgres_conn_id="SURFRIDERDB_WRITER_USER",
        sql='copy_trajectory_point_table.sql',
        dag=dag
    )

    compute_metrics_bi_temp_trajectory_point = PostgresOperator(
        task_id='compute_metrics_bi_temp_trajectory_point',
        postgres_conn_id="SURFRIDERDB_WRITER_USER",
        sql='compute_metrics_bi_temp_trajectory_point.sql',
        dag=dag
    )

    compute_metrics_bi_temp_campaign = PostgresOperator(
        task_id='compute_metrics_bi_temp_campaign',
        postgres_conn_id="SURFRIDERDB_WRITER_USER",
        sql='compute_metrics_bi_temp_campaign.sql',
        dag=dag
    )


    compute_bi_temp_trajectory_point_river = PostgresOperator(
        task_id='compute_bi_temp_trajectory_point_river',
        postgres_conn_id="SURFRIDERDB_WRITER_USER",
        sql='compute_bi_temp_trajectory_point_river.sql',
        dag=dag
    )

    compute_bi_temp_campaign_river = PostgresOperator(
        task_id='compute_bi_temp_campaign_river',
        postgres_conn_id="SURFRIDERDB_WRITER_USER",
        sql='compute_bi_temp_campaign_river.sql',
        dag=dag
    )

    add_metrics_bi_temp_campaign_river = PostgresOperator(
        task_id='add_metrics_bi_temp_campaign_river',
        postgres_conn_id="SURFRIDERDB_WRITER_USER",
        sql='add_metrics_bi_temp_campaign_river.sql',
        dag=dag
    )

    compute_metrics_bi_temp_trash = PostgresOperator(
        task_id='compute_metrics_bi_temp_trash',
        postgres_conn_id="SURFRIDERDB_WRITER_USER",
        sql='compute_metrics_bi_temp_trash.sql',
        dag=dag
    )

    compute_bi_temp_trash_river = PostgresOperator(
        task_id='compute_bi_temp_trash_river',
        postgres_conn_id="SURFRIDERDB_WRITER_USER",
        sql='compute_bi_temp_trash_river.sql',
        dag=dag
    )

    copy_bi_tables_to_bi_temp = PostgresOperator(
        task_id='copy_bi_tables_to_bi_temp',
        postgres_conn_id="SURFRIDERDB_WRITER_USER",
        sql='copy_bi_tables_to_bi_temp.sql',
        dag=dag
    )

    compute_metrics_bi_temp_river = PostgresOperator(
        task_id='compute_metrics_bi_temp_river',
        postgres_conn_id="SURFRIDERDB_WRITER_USER",
        sql='compute_metrics_bi_temp_river.sql',
        dag=dag
    )

    compute_metrics_bi_temp_segment = PostgresOperator(
        task_id='compute_metrics_bi_temp_segment',
        postgres_conn_id="SURFRIDERDB_WRITER_USER",
        sql='compute_metrics_bi_temp_segment.sql',
        dag=dag
    )

    update_bi_tables = PostgresOperator(
        task_id='update_bi_tables',
        postgres_conn_id="SURFRIDERDB_WRITER_USER",
        sql='update_bi_tables.sql',
        dag=dag
    )

    clean_bi_temp_tables = PostgresOperator(
        task_id='clean_bi_temp_tables',
        postgres_conn_id="SURFRIDERDB_WRITER_USER",
        sql='clean_bi_temp_tables.sql',
        dag=dag
    )

    logs_status_pipeline = PostgresOperator(
        task_id='logs_status_pipeline',
        postgres_conn_id="SURFRIDERDB_WRITER_USER",
        sql='logs_status_pipeline.sql',
        dag=dag
    )

    run_bi_postprocessing = TriggerDagRunOperator(
        task_id='run_bi_postprocessing',
        trigger_dag_id='bi-postprocessing',
        wait_for_completion=True,
        dag=dag
    )

get_new_campaign_ids >> [copy_campaign_table, copy_trash_table, copy_trajectory_point_table]
copy_trajectory_point_table >> compute_metrics_bi_temp_trajectory_point
compute_metrics_bi_temp_trajectory_point >> compute_bi_temp_trajectory_point_river
compute_bi_temp_trajectory_point_river >> compute_bi_temp_campaign_river

copy_trash_table >> compute_metrics_bi_temp_trash
[
    compute_bi_temp_campaign_river,
    compute_metrics_bi_temp_trash
] >> compute_bi_temp_trash_river

[
    copy_campaign_table,
    compute_metrics_bi_temp_trash,
    compute_metrics_bi_temp_trajectory_point
] >> compute_metrics_bi_temp_campaign



[
    compute_metrics_bi_temp_campaign,
    compute_bi_temp_trash_river,
] >> add_metrics_bi_temp_campaign_river

add_metrics_bi_temp_campaign_river >> copy_bi_tables_to_bi_temp

copy_bi_tables_to_bi_temp >> compute_metrics_bi_temp_river >> compute_metrics_bi_temp_segment
compute_metrics_bi_temp_segment >> update_bi_tables
update_bi_tables >> clean_bi_temp_tables
clean_bi_temp_tables >> logs_status_pipeline
logs_status_pipeline >> run_bi_postprocessing