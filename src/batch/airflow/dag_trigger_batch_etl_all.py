
import logging
import shutil
import time
from pprint import pprint

from numpy import column_stack

import pendulum

from airflow import DAG
from airflow.decorators import task
from airflow.sensors.python import PythonSensor
from airflow.operators.bash import BashOperator

from postgre import *
from exceptions import *

import os
import json
import pandas as pd
import requests
import logging
from postgre import get_pg_connection_string, open_pg_connection, close_pg_connection

logger = logging.getLogger()

doc_md_DAG = """
## ETL

This DAG triggers the ETL (extract, transform and load) on all containers.
This means it collects all .json files that were uploaded to the blob storage, through the mobile app.

#### How it works
When a user sends its data, the backend API stores the user data (json file, video, images) to a container (either `manual`, `mobile` for AI version, or `gopro`)
The API also adds lines in the database:
- in the `campaign.campaign` table
- in the `logs.etl` table, stating that the campaign is `notprocessed`

This DAG fills the DB with either the data from the json and/or the video processed by the AI.
The AI part will not be powered if there is no AI videos to be processed.

When it finishes successfully, it sets the campaigns in the `logs.etl` table to `processed`, or `failed`.

#### If it fails
- You can safely rerun this DAG, if it fails
- try to see which node made the process failing: is it the AI? The `trigger_batch_etl`?
- Check in the Airflow logs what is the error.

#### Maintainers
- Charles Ollion or Clément Le Roux
"""

with DAG(
    dag_id='trigger_batch_etl_all',
    schedule_interval='@weekly',
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=['plastico'],
    doc_md=doc_md_DAG
   ) as dag:

        # Parameters
        TENANT_ID = os.getenv('TENANT_ID')
        SUBSCRIPTION_ID = os.getenv('SUBSCRIPTION_ID')
        VALUE = os.getenv('VALUE')
        CLIENT_ID = os.getenv('CLIENT_ID')
        AKS_RG = os.getenv('AKS_RG')
        AKS_CLUSTER = os.getenv('AKS_CLUSTER')
        AKS_NODEPOOL = os.getenv('AKS_NODEPOOL')
        AI_URL = os.getenv('AI_URL')
        VIDEO_TEST_NAME = os.getenv('VIDEO_TEST_NAME')
        VIDEO_TEST_URL = os.getenv('VIDEO_TEST_URL')
        ETL_URL = os.getenv('ETL_URL')

        # PG connection
        pg_conn_string = get_pg_connection_string()
        pg_connection = open_pg_connection(pg_conn_string)
        pg_cursor = pg_connection.cursor()

        
        # [START scale_aks_nodepool]
        @task(task_id="scaleup_aks_nodepool")
        def scale_aks_nodepool(tenant_id,value,client_id,subscription,aks_rg,aks_cluster,aks_nodepool,scale):

            # azure oauth2 authentication
            url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"
            data = {'grant_type': 'client_credentials',
                    'client_secret': f'{value}',
                    'client_id': f'{client_id}',
                    'resource': 'https://management.azure.com'}
            try:
                response = requests.post(url, data=data)
            except:
                logging.info(f"There was an error when acquiring token {response.content}")

            token = response.json()['access_token']

            # scale aks nodepool
            headers = {"Content-Type":"application/json","Authorization":f"Bearer {token}"}
            url = f"https://management.azure.com/subscriptions/{subscription}/resourceGroups/{aks_rg}/providers/Microsoft.ContainerService/managedClusters/{aks_cluster}/agentPools/{aks_nodepool}?api-version=2022-02-01"
            data = {
            "properties": {
                "orchestratorVersion": "",
                "count": scale,
                "osType": "Linux",
                "creationData": {
                "sourceResourceId": f"/subscriptions/{subscription}/resourceGroups/{aks_rg}/providers/Microsoft.ContainerService/"
                }
                }
            }
            try:
                response = requests.put(url,data=json.dumps(data),headers=headers)
            except:
                logging.info(f"There was an error when scaling aks {response.content}")
                
            return str(response)
        
        scaleup_aks_nodepool_op = scale_aks_nodepool(TENANT_ID,VALUE,CLIENT_ID,SUBSCRIPTION_ID,AKS_RG,AKS_CLUSTER,AKS_NODEPOOL,1)
        # [END scaleup_aks_nodepool]


        # [START wait_surfnet_op]
        def wait_surfnet():
            ai_ready = False
            while (ai_ready == False):
                try:
                    response = requests.get(AI_URL+':8000')
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

        post_surfnet_video_op = post_video_surfnet(VIDEO_TEST_NAME,AI_URL)
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
                media_logid = media[0]
                media_dico = {'name':media_name,'container':media_container,'logid':media_logid}
                notprocessed_media_list.append(media_dico)


            # Batch ETL on not processed media
            output_list = []
            for notprocessed_media in notprocessed_media_list:
                blob_name = notprocessed_media['name']
                container = notprocessed_media['container']
                logid = notprocessed_media['logid']
                url = f'{ETL_URL}:80/api/etlHttpTrigger?container={container}&blob={blob_name}&prediction=ai&source={container}&target=postgre&aiurl={AI_URL}&logid={logid}'
                response = requests.get(url)
                if not response.ok:
                    print(f'Request to ETL failed wih reason {response.reason}.')
                output = [response._content]
                output_list.append(output)
            
            return str(output_list)

        trigger_batch_etl_op = trigger_batch_etl(pg_cursor)
        # [END trigger_batch_etl]


        # [START scaledown_aks_nodepool]
        @task(task_id="scaledown_aks_nodepool")
        def scale_aks_nodepool(tenant_id,value,client_id,subscription,aks_rg,aks_cluster,aks_nodepool,scale):

            # azure oauth2 authentication
            url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"
            data = {'grant_type': 'client_credentials',
                    'client_secret': f'{value}',
                    'client_id': f'{client_id}',
                    'resource': 'https://management.azure.com'}
            try:
                response = requests.post(url, data=data)
            except:
                logging.info(f"There was an error when acquiring token {response.content}")

            token = response.json()['access_token']

            # scale aks nodepool
            headers = {"Content-Type":"application/json","Authorization":f"Bearer {token}"}
            url = f"https://management.azure.com/subscriptions/{subscription}/resourceGroups/{aks_rg}/providers/Microsoft.ContainerService/managedClusters/{aks_cluster}/agentPools/{aks_nodepool}?api-version=2022-02-01"
            data = {
            "properties": {
                "orchestratorVersion": "",
                "count": scale,
                "osType": "Linux",
                "creationData": {
                "sourceResourceId": f"/subscriptions/{subscription}/resourceGroups/{aks_rg}/providers/Microsoft.ContainerService/"
                }
                }
            }
            try:
                response = requests.put(url,data=json.dumps(data),headers=headers)
            except:
                logging.info(f"There was an error when scaling aks {response.content}")
                
            return str(response)
        
        scaledown_aks_nodepool_op = scale_aks_nodepool(TENANT_ID,VALUE,CLIENT_ID,SUBSCRIPTION_ID,AKS_RG,AKS_CLUSTER,AKS_NODEPOOL,0)
        # [END scaledown_aks_nodepool]
    
        scaleup_aks_nodepool_op >> wait_surfnet_op >> get_surfnet_video_op >> post_surfnet_video_op >> trigger_batch_etl_op >> scaledown_aks_nodepool_op


        
        