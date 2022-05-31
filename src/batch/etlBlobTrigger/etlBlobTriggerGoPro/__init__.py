import logging
import os
import requests

import azure.functions as func
from .postgre import get_log_df, get_pg_connection_string, open_pg_connection, insert_log_etl_df

logging.basicConfig(level=logging.INFO)


def main(etlblob: func.InputStream):
    logging.info(f"Python blob trigger function processed blob \n"
                 f"Name: {etlblob.name}\n"
                 f"Blob Size: {etlblob.length} bytes")
    # Blob info
    blob_fullname = etlblob.name
    container = blob_fullname.split('/')[0]
    blob_name = blob_fullname.split('/')[1]
    # Media info
    campaign_id = os.path.splitext(blob_name)[0]
    media_name = blob_name
    media_id = campaign_id
    # Log Dataframe
    etl_log_df = get_log_df(campaign_id,media_id,media_name)
    # PG connection
    pg_conn_string = get_pg_connection_string()
    pg_connection = open_pg_connection(pg_conn_string)
    pg_cursor = pg_connection.cursor()
    # Log insert
    for i, row in etl_log_df.iterrows():
        try:
            log_id = insert_log_etl_df(row,pg_cursor,pg_connection,'gopro')
            logging.info(f'Successfully insterted new log: {log_id}')
        except:
            log_id = row['campaign_id']
            logging.error(f'There was an issue inserting log id: {log_id} within PostGre')
            logging.error("Early exit of ETL workflow as PG INSERT failed")
            exit()    