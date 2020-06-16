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

        
        pg_conn_string = get_pg_connection_string()
        pg_connection = open_pg_connection(pg_conn_string)
        pg_cursor = pg_connection.cursor()


        logger.info('############################################################')
        logger.info('################   Plastic Origin ETL End   ################')
        logger.info('############################################################')

        output = func.HttpResponse(f'Congratulations, you have successfully made prediction from container name: {campaign_container_name}, blobname: {blob_video_name} with AI service !')
        return output

    else:
        return func.HttpResponse(
             "Please pass a container name and blob name and video name and aiurl",
             status_code=400
        )

# Local
#?containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com&source=ai
# AI
#http://localhost:7072/api/pgHttpTriggerNew?containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com&source=ai&target=csv
#http://localhost:7072/api/pgHttpTriggerNew?containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com&source=ai&target=postgre
# JSON
#http://localhost:7072/api/pgHttpTriggerNew?containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com&source=json&target=csv
#http://localhost:7072/api/pgHttpTriggerNew?containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com&source=json&target=csv

# Azure
#&containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com
#https://azfunplasticoetl.azurewebsites.net/api/aiHttpTrigger?code=/Ixlz/BmpcNtyEu3NXKUvNsauf9SjKuEz0cqH/ro6uv62oy4uzbv3Q==&containername=campaign0&blobname=28022020_Boudigau_4_short_480.mov&videoname=28022020_Boudigau_4.MP4&aiurl=http://aiapiplastico-dev.westeurope.cloudapp.azure.com