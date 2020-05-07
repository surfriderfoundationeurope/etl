import logging
import azure.functions as func
# import prerequesite for blob_ops
from azure.storage.blob import ContainerClient
from azure.storage.blob import BlobClient
from .blob_ops import blobInContainer,blobInfos,downloadBlob
# import prerequesite for ai_ops
import json 
import logging
import requests
from .ai_ops import AIready,getPrediction,jsonPrediction,getTrashLabel,mapLabel2TrashIdPG
# extra import
import os

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    containername = req.params.get('containername')
    blobname = req.params.get('blobname')
    videoname = req.params.get('videoname')
    aiurl = req.params.get('aiurl')

    if containername and blobname and videoname and aiurl:
        print('############################################################')
        print('################ Plastic Origin ETL process ################')
        print('################  Let\'s predict some Trash  ################')
        print('############################################################')
        print('\n')

        print('###################### Pipeline Step0 ######################')
        print('################ Get Video from Azure Storage ##############')
        # blob storage connection string
        connection_string = os.getenv("CONN_STRING")

        # get list of blobs in container campaign0
        campaign_container_name = containername
        blobs_campaign0 = blobInContainer(connection_string,campaign_container_name)
        print("Blobs in container:")
        print(blobs_campaign0)

        # get infos of blob 'goproshort-480p.mov' '28022020_Boudigau_4_short.mp4'
        blob_video_name = blobname   
        blobInfos(connection_string,campaign_container_name,blob_video_name)

        # download locally in /tmp blob video
        blob_video = BlobClient.from_connection_string(conn_str=connection_string,container_name=campaign_container_name, blob_name=blob_video_name)
        downloadBlob(blob_video)

        print('###################### Pipeline Step1bis ###################')
        print('##################### AI Trash prediction ##################')

        isAIready = AIready(f'{aiurl}:5000')

        if isAIready == True:
            prediction = getPrediction(blob_video_name,aiurl)
        else:
            print("Early exit of ETL workflow as AI service is not available")
            exit()

        # cast prediction to JSON/Dictionnary format
        json_prediction = jsonPrediction(prediction)

        
        print('############################################################')
        print('################  AI Prediction End   ################')
        print('############################################################')

        output = func.HttpResponse(f'Congratulations, you have successfully made prediction from container name: {containername}, blobname: {blobname}, video name: {videoname} with AI service !')
        return output

    else:
        return func.HttpResponse(
             "Please pass a container name and blob name and video name and aiurl",
             status_code=400
        )

#?containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com
#&containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com
#http://localhost:7071/api/aiHttpTrigger?containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com
#https://azfunplasticoetl.azurewebsites.net/api/aiHttpTrigger?code=/Ixlz/BmpcNtyEu3NXKUvNsauf9SjKuEz0cqH/ro6uv62oy4uzbv3Q==&containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com
#https://azfunplasticoetl.azurewebsites.net/api/aiHttpTrigger?code=/Ixlz/BmpcNtyEu3NXKUvNsauf9SjKuEz0cqH/ro6uv62oy4uzbv3Q==&containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com