import logging
import azure.functions as func
# import prerequesite for blob_ops
from azure.storage.blob import ContainerClient
from azure.storage.blob import BlobClient
from .utils.blob import download_blob
# import prerequesite for ai_ops
import json 
import logging
import requests
from .utils.ai import is_ai_ready,get_prediction,get_json_prediction,get_trash_label,map_label_to_trash_id_PG
# extra import
import os

logger = logging.getLogger()

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    container_name = req.params.get('containername')
    blob_video_name = req.params.get('blobname')
    source_data = req.params.get('source')
    ai_url = req.params.get('aiurl')

    if container_name and blob_video_name and ai_url:
        logger.info('############################################################')
        logger.info('################ Plastic Origin ETL process ################')
        logger.info('################  Let\'s predict some Trash  ################')
        logger.info('############################################################')

        logger.info('###################### Pipeline Step0 ######################')
        logger.info('################ Get Video from Azure Storage ##############')
        # blob storage connection string
        connection_string = os.getenv("CONN_STRING")

        # Download locally in /tmp blob video
        blob_video = BlobClient.from_connection_string(conn_str=connection_string,container_name=container_name, blob_name=blob_video_name)
        download_blob(blob_video)

        logger.info('###################### Pipeline Step1bis ###################')
        logger.info('################## Get Trash Prediction Data ################')

        if source_data == 'ai':
            ai_ready = is_ai_ready(f'{ai_url}:5000')
            if ai_ready == True:
                prediction = get_prediction(blob_video_name,f'{ai_url}:5000')
            else:
                logger.info("Early exit of ETL workflow as AI service is not available")
                exit()
            # Cast prediction to JSON/Dictionnary format
            json_prediction = get_json_prediction(prediction)
            logger.info("Have json prediction")

        elif source_data == 'json':
            prediction_path = '../../data/prediction.json'
            with open(prediction_path) as json_file:
                json_prediction = json.load(json_file)

        
        logger.info('############################################################')
        logger.info('###################  AI Prediction End   ###################')
        logger.info('############################################################')

        output = func.HttpResponse(f'Congratulations, you have successfully made prediction from container name: {container_name}, blobname: {blob_video_name} with AI service !')
        return output

    else:
        return func.HttpResponse(
             "Please pass a container name and blob name and video name and aiurl",
             status_code=400
        )

# Local
#?containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com&source=ai
#http://localhost:7072/api/etlHttpTriggerNew?containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com&source=json&target=csv
#http://localhost:7072/api/etlHttpTriggerNew?containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com&source=json&target=postgre
# Azure
#&containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com
#https://azfunplasticoetl.azurewebsites.net/api/aiHttpTrigger?code=/Ixlz/BmpcNtyEu3NXKUvNsauf9SjKuEz0cqH/ro6uv62oy4uzbv3Q==&containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com