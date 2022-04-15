
import logging
import shutil
import time
from pprint import pprint

from numpy import column_stack

import pendulum

from airflow import DAG
from airflow.decorators import task
from airflow.sensors.python import PythonSensor

from postgre import *
from exceptions import *

import os
import json
import pandas as pd
import requests
import logging
from postgre import get_pg_connection_string, open_pg_connection, close_pg_connection

logger = logging.getLogger()


with DAG(
    dag_id='trigger_batch_etl',
    schedule_interval=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=['plastico'],
   ) as dag:

        # Parameters
        AI_DEV_URL = os.getenv('AI_DEV_URL')
        VIDEO_TEST_NAME = os.getenv('VIDEO_TEST_NAME')
        VIDEO_TEST_URL = os.getenv('VIDEO_TEST_URL')
        ETL_DEV_URL = os.getenv('ETL_DEV_URL')

        # PG connection
        pg_conn_string = get_pg_connection_string()
        pg_connection = open_pg_connection(pg_conn_string)
        pg_cursor = pg_connection.cursor()


        # [START wait_surfnet_op]
        def wait_surfnet():
            ai_ready = False
            while (ai_ready == False):
                try:
                    response = requests.get(AI_DEV_URL+':8000')
                    output = [response.status_code][0]
                    if output == 200:
                        ai_ready = True
                        logger.info('AI is ready now!')
                except:
                    pass
                    logger.info('AI is not ready yet!')
            return ai_ready

        wait_surfnet_op = PythonSensor(
        task_id='wait_surfnet',
        python_callable=wait_surfnet,
        )
        # [END wait_surfnet_op]

        # [START get_surfnet_video]
        @task(task_id="get_surfnet_video")
        def get_surfnet_video(video_url,video_name):
            response = requests.get(video_url)
            open(video_name, 'wb').write(response.content)

        get_surfnet_video_op = get_surfnet_video(VIDEO_TEST_URL,VIDEO_TEST_NAME)
        # [END get_surfnet_video]

        # [START post_surfnet_video]
        @task(task_id="post_surfnet_video")
        def post_video_surfnet(video_name,ai_url):
            files = {'file': (video_name, open(video_name, 'rb'), 'application/octet-stream')}
            response = requests.post(ai_url+':8000', files=files)
            if not response.ok:
                logger.error(f'Request to AI failed wih reason {response.reason}.')
            output = [response._content]
            return str(output)

        post_surfnet_video_op = post_video_surfnet(VIDEO_TEST_NAME,AI_DEV_URL)
        # [END post_surfnet_video]

        # [START trigger_batch_etl]
        @task(task_id="trigger_batch_etl")
        
        def trigger_batch_etl(cursor):
            # Get notprocessed media
            cursor.execute("SELECT * FROM logs.etl WHERE status = 'notprocessed'")
            query_output = cursor.fetchall()
            notprocessed_media = query_output

            # List not processed media name & container
            notprocessed_media_list = []
            for media in notprocessed_media:
                media_name = media[3]
                media_container = media[10]
                media_dico = {'name':media_name,'container':media_container}
                notprocessed_media_list.append(media_dico)

            # Batch ETL on not processed media
            output_list = []
            for notprocessed_media in notprocessed_media_list:
                blob_name = notprocessed_media['name']
                container = notprocessed_media['container']
                url = f'{ETL_DEV_URL}:80/api/etlHttpTrigger?container={container}&blob={blob_name}&prediction=ai&source={container}&target=postgre&aiurl={AI_DEV_URL}'
                response = requests.get(url)
                if not response.ok:
                    print(f'Request to ETL failed wih reason {response.reason}.')
                output = [response._content]
                output_list.append(output)
            
            return str(output_list)

        trigger_batch_etl_op = trigger_batch_etl(pg_cursor)
        
        # [END trigger_batch_etl]
    
        wait_surfnet_op >> get_surfnet_video_op >> post_surfnet_video_op >> trigger_batch_etl_op


        
        