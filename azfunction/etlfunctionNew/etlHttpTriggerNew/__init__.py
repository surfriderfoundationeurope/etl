import azure.functions as func

# import prerequesite for blob
from azure.storage.blob import ContainerClient
from azure.storage.blob import BlobClient
from .utils.blob import list_blob_in_container,get_blob_infos,download_blob
# import prerequesite for ai
import json
import requests
import logging
from .utils.ai import is_ai_ready,get_prediction,get_json_prediction,get_clean_timed_prediction,get_trash_label,map_label_to_trash_id_PG,get_trash_first_time,get_trash_time_index,get_df_prediction
# import prerequesite for gps
import gpxpy
import gpxpy.gpx
import json
import subprocess
import datetime
from datetime import datetime
from datetime import timedelta
from shapely.geometry import Point
from functools import partial
import pyproj
from shapely.ops import transform
from tqdm import tqdm
from .utils.gps import extract_gpx_from_gopro,parse_gpx,get_gps_point_list,create_time,create_latitude,create_longitude,create_elevation,fill_gps,long_lat_to_shape_point,transform_geo,get_df_trash_gps
# import prerequesite from media
from .utils.media import get_media_duration,get_media_fps
# import prerequesite for postgre
import os
import psycopg2
from .utils.postgre import get_pg_connection_string,open_pg_connection,close_pg_connection,insert_trash_2,insert_trash_df,get_df_data
# import exception
from .utils.exceptions import ETLError
import warnings
warnings.filterwarnings('ignore')
# import argparse to pass parameters to main function
import argparse
import pathlib

DOWNLOAD_PATH = '/tmp'
AI_PORT = '5000'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    campaign_container_name = req.params.get('containername')
    blob_video_name = req.params.get('blobname')
    source_data = req.params.get('source')
    ai_url = req.params.get('aiurl')
    target_store = req.params.get('target')
    video_name = req.params.get('videoname')

    if campaign_container_name and blob_video_name and ai_url and source_data and target_store and video_name:

        connection_string = os.getenv("CONN_STRING")
        pgserver = os.getenv("PGSERVER")
        pgdatabase = os.getenv("PGDATABASE")
        pgusername = os.getenv("PGUSERNAME")
        pgpassword = os.getenv("PGPWD")

        if None in [connection_string]:
            raise ETLError("Could not find Azure Storage connection string in environment")
        if target_store == 'postgre' and None in [pgserver, pgdatabase, pgusername, pgpassword]:
            raise ETLError("Could not find Postgre variable in environment. ")


        # Entering ETL process
        logger.info('############################################################')
        logger.info('################ Plastic Origin ETL process ################')
        logger.info('################  Let\'s predict some Trash  ################')
        logger.info('############################################################')
        logger.info('###################### Pipeline Step0 ######################')
        logger.info('################ Get Video from Azure Storage ##############')

        # Download Blob video from Azure
        if not video_name in os.listdir(DOWNLOAD_PATH):
            blob_video_client = BlobClient.from_connection_string(conn_str=connection_string,container_name=campaign_container_name, blob_name=blob_video_name)
            download_blob(blob_video_client,DOWNLOAD_PATH)

        # Get AI prediction
        logger.info('###################### Pipeline Step1bis ###################')
        logger.info('################## Get Trash Prediction Data ################')

        # From AI inference server
        if source_data == 'ai':
            # Test that AI service is ready
            ai_ready = is_ai_ready(f'{ai_url}:5000')
            if ai_ready == True:
                prediction = get_prediction(blob_video_name,f'{ai_url}:5000')
            else:
                logger.info("Early exit of ETL workflow as AI service is not available")
                exit()
            # Cast prediction to JSON/Dictionnary format
            json_prediction = get_json_prediction(prediction)

        # From JSON file
        elif source_data == 'json':
            with open(pathlib.Path(__file__).parent / 'prediction.json') as json_file:
                json_prediction = json.load(json_file)

        # GPS pipeline
        logger.info('###################### Pipeline Step1 ######################')
        logger.info('######################  Get GPX Data  ######################')
        before = datetime.now()
        gpx_path = extract_gpx_from_gopro(f'/tmp/{video_name}')
        after = datetime.now()
        delta = after - before
        logger.info(delta)
        # GPX parsing
        gpx_data = parse_gpx(gpx_path)
        # GPS Points
        gps_points = get_gps_point_list(gpx_data)
        # Video duration
        video_duration = get_media_duration(f'/tmp/{video_name}')
        logger.info(f'Video duration in second from metadata:{video_duration}')
        media_fps = get_media_fps(f'/tmp/{video_name}')
        # media_fps = int(json_prediction['fps'])
        # GPS file duration
        timestamp_delta = gps_points[len(gps_points)-1]['Time'] - gps_points[0]['Time']
        logger.info(f'GPS file time coverage in second:{timestamp_delta.seconds}')

        logger.info('###################### Pipeline Step2 ######################')
        logger.info('#####################   Get GPS Data   #####################')
        video_duration_sup = int(video_duration)+1
        gps_points_filled = fill_gps(gps_points,video_duration_sup)

        logger.info('###################### Pipeline Step3 ######################')
        logger.info('################ Store Data in PostGre or CSV ##############')
        
        # INSERTING all detected_trash within PostGre
        # WITH DATAFRAME
        # Create Dataframe
        df_predictions = get_df_prediction(json_prediction,media_fps) 
        df_trash_gps = get_df_trash_gps(df_predictions,gps_points_filled)
        df_data = get_df_data(df_predictions,df_trash_gps)

        if target_store == 'postgre':
            # Get connection string information from env variables
            pg_conn_string = get_pg_connection_string()
            pg_connection = open_pg_connection(pg_conn_string)
            pg_cursor = pg_connection.cursor()
            # Store row_id when insert
            row_id_list = []

            for i,row in tqdm(df_data.iterrows()):
                try:
                    row_id = insert_trash_df(row,pg_cursor,pg_connection)
                    logger.info(row_id)
                    row_id_list.append(row_id)
                except:
                    prediction_id = row['id']
                    logger.error(f'There was an issue inserting Trash id: {prediction_id} within PostGre')
                    logger.error("Early exit of ETL workflow as PG INSERT failed")
                    exit()

            logger.info(f'Successfully inserted {str(len(row_id_list))} Trashes within Trash table')
            output = func.HttpResponse(f'Congratulations, you have predicted trashes with AI and made insert within PostGre ! row_id list: {row_id_list}')
    

            # Close PG connection
            close_pg_connection(pg_connection)

        elif target_store == 'csv':
            export_path='/tmp/dataexport.csv'
            df_data.to_csv(export_path, encoding='utf-8')
            logger.info(f'exporting trash data to {export_path}')
            output = func.HttpResponse(f'Congratulations, you have predicted trashes with AI and made CSV export to /tmp/dataexport.csv')


        logger.info('############################################################')
        logger.info('################   Plastic Origin ETL End   ################')
        logger.info('############################################################')

        #output = func.HttpResponse(f'Congratulations, you have successfully made prediction from container name: {campaign_container_name}, blobname: {blob_video_name} with AI service !')
        return output

    else:
        return func.HttpResponse(
             "Please pass a container name and blob name and video name and aiurl",
             status_code=400
        )

# Local
#?containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com&source=ai
# AI
#http://localhost:7072/api/etlHttpTriggerNew?containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com&source=ai&target=csv
#http://localhost:7072/api/etlHttpTriggerNew?containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com&source=ai&target=postgre
# JSON
#http://localhost:7072/api/etlHttpTriggerNew?containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com&source=json&target=csv
#http://localhost:7072/api/etlHttpTriggerNew?containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com&source=json&target=postgre

# Azure
#&containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com
# https://azfunplasticoeltapp.azurewebsites.net/api/etlHttpTriggerNew?code=rdLjseVObYmVWPUnmxL2YdGy6byiTe0VfdB5BB6gOH0gRbWoM4wZzQ==&containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com&source=json&target=postgre
# https://azfunplasticoeltapp.azurewebsites.net/api/etlHttpTriggerNew?code=rdLjseVObYmVWPUnmxL2YdGy6byiTe0VfdB5BB6gOH0gRbWoM4wZzQ==&containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com&source=json&target=csv


#http://azfunplasticoetldock.azurewebsites.net/api/etlHttpTriggerNew?code=nWeWfFkxDnvuH8SxjaGBdfLGsQLSLx/2aOKON3SNoWW9IP/y0aUArg==&containername=campaign0&blobname=28022020_Boudigau_4.MP4&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com&source=json&target=csv