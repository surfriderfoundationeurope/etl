import argparse
import datetime
import json
import logging
import os
import pathlib
import subprocess
import warnings
from datetime import datetime, timedelta
from functools import partial

import requests
from tqdm import tqdm

import gpxpy
import gpxpy.gpx
import psycopg2
import pyproj
from azure.storage.blob import BlobClient, ContainerClient
from shapely.geometry import Point
from shapely.ops import transform
from utils.ai import (get_clean_timed_prediction, get_df_manual_trash,
                      get_df_prediction, get_json_prediction, get_prediction,
                      get_trash_first_time, get_trash_label,
                      get_trash_time_index, is_ai_ready,
                      map_label_to_trash_id_PG)
from utils.blob import download_blob, get_blob_infos, list_blob_in_container
from utils.exceptions import ETLError
from utils.gps import (create_elevation, create_latitude, create_longitude,
                       create_time, extract_gpx_from_gopro, fill_gps,
                       get_df_manual_gps, get_df_trash_gps, get_gps_point_list,
                       get_gpx_name, long_lat_to_shape_point, parse_gpx,
                       transform_geo)
from utils.media import get_media_duration, get_media_fps
from utils.postgre import (close_pg_connection, get_df_data,
                           get_pg_connection_string, insert_trash_2,
                           insert_trash_df, open_pg_connection)

warnings.filterwarnings('ignore')

# Settings
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Constant
DOWNLOAD_PATH = '/tmp'
AI_PORT = '5000'

#### Main definition ####


def main(argv):
    # init variables from argparse
    ai_url = argv.aiurl
    blob_name = argv.blobname
    container_name = argv.containername
    prediction_source = argv.prediction
    source_data = argv.source
    target_store = argv.target

    # Early check that ai url is given if prediction_source is ai
    if prediction_source == 'ai' and ai_url == None:
        parser.error("--prediction ai requires --aiurl argument")

    else:
        # Eary check that environment variables are set
        connection_string = os.getenv("CONN_STRING")
        pgserver = os.getenv("PGSERVER")
        pgdatabase = os.getenv("PGDATABASE")
        pgusername = os.getenv("PGUSERNAME")
        pgpassword = os.getenv("PGPWD")
        if None in [connection_string]:
            raise ETLError(
                "Could not find Azure Storage connection string in environment")
        if target_store == 'postgre' and None in [pgserver, pgdatabase, pgusername, pgpassword]:
            raise ETLError("Could not find Postgre variable in environment. ")

        # Entering ETL process
        logger.info(
            '############################################################')
        logger.info(
            '################ Plastic Origin ETL process ################')
        logger.info(
            '################  Let\'s predict some Trash  ################')
        logger.info(
            '############################################################')
        logger.info(
            '###################### Pipeline Step0 ######################')
        logger.info(
            '################ Get Video from Azure Storage ##############')

        # Download Blob video from Azure
        if source_data == 'gopro' or source_data == 'mobile':
            # Download only if not yet downloaded
            if not blob_name in os.listdir(DOWNLOAD_PATH):
                blob_video_client = BlobClient.from_connection_string(
                    conn_str=connection_string, container_name=container_name, blob_name=blob_name)
                download_blob(blob_video_client, DOWNLOAD_PATH)
            if source_data == 'mobile':
                blob_gpx_name = get_gpx_name(blob_name)
                if not blob_gpx_name in os.listdir(DOWNLOAD_PATH):
                    blob_gpx_client = BlobClient.from_connection_string(
                        conn_str=connection_string, container_name=container_name, blob_name=blob_gpx_name)
                    download_blob(blob_gpx_client, DOWNLOAD_PATH)
        elif source_data == 'manual':
            blob_gpx_name = get_gpx_name(blob_name)
            if not blob_gpx_name in os.listdir(DOWNLOAD_PATH):
                blob_gpx_client = BlobClient.from_connection_string(
                    conn_str=connection_string, container_name=container_name, blob_name=blob_gpx_name)
                download_blob(blob_gpx_client, DOWNLOAD_PATH)

        # Get AI prediction
        logger.info(
            '###################### Pipeline Step1bis ###################')
        logger.info(
            '################# Get Trash Prediction Data ################')

        if source_data == 'gopro' or source_data == 'mobile':
            # From AI inference server
            if prediction_source == 'ai':
                # Test that AI service is ready
                ai_ready = is_ai_ready(f'{ai_url}:{AI_PORT}')
                if ai_ready == True:
                    prediction = get_prediction(
                        blob_name, f'{ai_url}:{AI_PORT}')
                else:
                    logger.info(
                        "Early exit of ETL workflow as AI service is not available")
                    exit()
                # Cast prediction to JSON/Dictionnary format
                json_prediction = get_json_prediction(prediction)

            # From JSON file
            elif prediction_source == 'json':
                with open(pathlib.Path(__file__).parent / '../datasample/prediction.json') as json_file:
                    json_prediction = json.load(json_file)

        # GPS pipeline
        logger.info(
            '###################### Pipeline Step1 ######################')
        logger.info(
            '######################  Get GPX Data  ######################')

        if source_data == 'gopro':
            gpx_path = extract_gpx_from_gopro(f'{DOWNLOAD_PATH}/{blob_name}')
        elif source_data == 'mobile' or source_data == 'manual':
            gpx_path = f'{DOWNLOAD_PATH}/{blob_gpx_name}'

        # GPX parsing
        gpx_data = parse_gpx(gpx_path)

        # GPS Points
        if source_data == 'gopro' or source_data == 'mobile':
            gps_points = get_gps_point_list(gpx_data)  # full list of gps point
        elif source_data == 'manual':
            gps_points = gpx_data.waypoints  # list of gps point with trash

        # Video duration
        if source_data == 'gopro' or source_data == 'mobile':
            video_duration = get_media_duration(f'{DOWNLOAD_PATH}/{blob_name}')
            media_fps = get_media_fps(json_prediction)

        logger.info(
            '###################### Pipeline Step2 ######################')
        logger.info(
            '#####################   Get GPS Data   #####################')
        if source_data == 'gopro' or source_data == 'mobile':
            video_duration_sup = int(video_duration)+1
            gps_points_filled = fill_gps(gps_points, video_duration_sup)

        logger.info(
            '###################### Pipeline Step3 ######################')
        logger.info(
            '################ Store Data in PostGre or CSV ##############')

        # INSERTING all detected_trash within PostGre

        # Create Dataframe
        if source_data == 'gopro' or source_data == 'mobile':
            df_predictions = get_df_prediction(json_prediction, media_fps)
            df_trash_gps = get_df_trash_gps(df_predictions, gps_points_filled)
            df_data = get_df_data(df_predictions, df_trash_gps)
        elif source_data == 'manual':
            df_manual_gps = get_df_manual_gps(gps_points)
            df_manual_trash = get_df_manual_trash(gps_points)
            df_data = get_df_data(df_manual_trash, df_manual_gps)

        # Store Data
        if target_store == 'postgre':
            # Get connection string information from env variables
            pg_conn_string = get_pg_connection_string()
            pg_connection = open_pg_connection(pg_conn_string)
            pg_cursor = pg_connection.cursor()
            # Store row_id when insert
            row_id_list = []

            for i, row in tqdm(df_data.iterrows()):
                try:
                    row_id = insert_trash_df(row, pg_cursor, pg_connection)
                    logger.info(row_id)
                    row_id_list.append(row_id)
                except:
                    prediction_id = row['id']
                    logger.error(
                        f'There was an issue inserting Trash id: {prediction_id} within PostGre')
                    logger.error(
                        "Early exit of ETL workflow as PG INSERT failed")
                    exit()

            logger.info(
                f'Successfully inserted {str(len(row_id_list))} Trashes within Trash table')

            # Close PG connection
            close_pg_connection(pg_connection)

        elif target_store == 'csv':
            export_path = f'{DOWNLOAD_PATH}/data.csv'
            df_data.to_csv(export_path, encoding='utf-8')
            logger.info(f'exporting trash data to {export_path}')

        logger.info(
            '############################################################')
        logger.info(
            '################   Plastic Origin ETL End   ################')
        logger.info(
            '############################################################')


##### Main Execution ####
# Defining parser
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--containername', required=True,
                    help='container name to get blob info from and download blob from to be processed by ETL')
parser.add_argument('-b', '--blobname', required=True,
                    help='blob name to be downloaded from azure blob storage campaign0 container into {DOWNLOAD_PATH}')
parser.add_argument(
    '-a', '--aiurl', help='url endpoint where AI inference service can be reached')
parser.add_argument('-p', '--prediction', choices=['ai', 'json'], default='ai',
                    help='specify whether prediction source comes from AI inference or local JSON file')
parser.add_argument('-s', '--source', choices=['gopro', 'mobile', 'manual'], default='gopro',
                    help='specify whether data source comes from gopro, mobile app or manual file')
parser.add_argument('-t', '--target', choices=['postgre', 'csv'], default='postgre',
                    help='specify whether to insert within postgre DB or export to csv file as data target')

# Create args parsing standard input
args = parser.parse_args()

# Run main
if __name__ == '__main__':
    main(args)
