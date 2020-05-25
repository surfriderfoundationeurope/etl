# import prerequesite for blob
from azure.storage.blob import ContainerClient
from azure.storage.blob import BlobClient
from utils.blob import list_blob_in_container,get_blob_infos,download_blob
# import prerequesite for ai
import json
import requests
import logging
from utils.ai import is_ai_ready,get_prediction,get_json_prediction,get_clean_timed_prediction,get_trash_label,map_label_to_trash_id_PG,get_trash_first_time,get_trash_time_index,get_df_prediction
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
from utils.gps import extract_gpx_from_gopro,parse_gpx,get_gps_point_list,create_time,create_latitude,create_longitude,create_elevation,fill_gps,long_lat_to_shape_point,transform_geo,get_df_trash_gps
# import prerequesite from media
from utils.media import get_media_duration,get_media_fps
# import prerequesite for postgre
import os
import psycopg2
from utils.postgre import get_pg_connection_string,open_pg_connection,close_pg_connection,insert_trash_2,insert_trash_df,get_df_data
import warnings
warnings.filterwarnings('ignore')
# import argparse to pass parameters to main function
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

#### Main definition ####
def main(argv):

    logger.info('############################################################')
    logger.info('################ Plastic Origin ETL process ################')
    logger.info('################  Let\'s predict some Trash  ################')
    logger.info('############################################################')
    logger.info('###################### Pipeline Step0 ######################')
    logger.info('################ Get Video from Azure Storage ##############')
    # Download Blob video from Azure
    connection_string = os.getenv("CONN_STRING")
    campaign_container_name = argv.containername
    blob_video_name = argv.blobname   
    blob_video = BlobClient.from_connection_string(conn_str=connection_string,container_name=campaign_container_name, blob_name=blob_video_name)
    download_blob(blob_video)

    # Get AI prediction from AI inference server
    logger.info('###################### Pipeline Step1bis ###################')
    logger.info('##################### AI Trash prediction ##################')
    ai_ready = is_ai_ready(f'{argv.aiurl}:5000')
    '''
    if ai_ready == True:
        prediction = get_prediction(blob_video_name,f'{argv.aiurl}:5000')
    else:
        logger.info("Early exit of ETL workflow as AI service is not available")
        exit()
  
    # Cast prediction to JSON/Dictionnary format
    json_prediction = get_json_prediction(prediction)

    # Optionnal json_prediction from local file
    '''
    with open('../data/prediction.json') as json_file:
        json_prediction = json.load(json_file)


    # GPS pipeline
    logger.info('###################### Pipeline Step1 ######################')
    logger.info('######################  GPX creation  ######################')
    video_name = argv.videoname
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
    logger.info("\n")
    video_duration = get_media_duration(f'/tmp/{video_name}')
    logger.info(f'Video duration in second from metadata:{video_duration}')
    media_fps = get_media_fps(f'/tmp/{video_name}')
    # GPS file duration
    timestamp_delta = gps_points[len(gps_points)-1]['Time'] - gps_points[0]['Time']
    logger.info(f'GPS file time coverage in second:{timestamp_delta.seconds}')

    logger.info('###################### Pipeline Step2 ######################')
    logger.info('################## Add missing GPS points ##################')
    video_duration_sup = int(video_duration)+1
    gps_points_filled = fill_gps(gps_points,video_duration_sup)

    logger.info('###################### Pipeline Step3 ######################')
    logger.info('################### Insert within PostGre ##################')
    # Get connection string information from env variables
    pg_conn_string = get_pg_connection_string()
    pg_connection = open_pg_connection(pg_conn_string)
    pg_cursor = pg_connection.cursor()

    # INSERTING all detected_trash within PostGre
    row_id_list = []
    '''
    for prediction in tqdm(json_prediction['detected_trash']):
        try:    
            # get trash_gps from gps module
            #time_index = get_trash_time_index(prediction)
            time_index = get_trash_time_index(prediction,media_fps)
            trash_gps = gps_points_filled[time_index]
            shape_trash_gps = long_lat_to_shape_point(trash_gps)
            geo_2154 = transform_geo(shape_trash_gps)
            geo_2154_trash_gps = {'Time': shape_trash_gps['Time'], 'the_geom': geo_2154,'Latitude':shape_trash_gps['Latitude'],'Longitude':shape_trash_gps['Longitude'], 'Elevation': shape_trash_gps['Elevation']}
            # get trash_type from ai module
            label = get_trash_label(prediction)
            trash_type = map_label_to_trash_id_PG(label)
            # insert trash from postgre module
            row_id = insert_trash_2(geo_2154_trash_gps,trash_type,pg_cursor,pg_connection)
            logger.info(row_id)
            row_id_list.append(row_id)
        except:
            prediction_id = prediction['id']
            logger.error(f'There was an issue inserting Trash id: {prediction_id} within PostGre')
            logger.error("Early exit of ETL workflow as PG INSERT failed")
            exit()
        '''
    df_predictions = get_df_prediction(json_prediction,media_fps) 
    df_trash_gps = get_df_trash_gps(df_predictions,gps_points_filled)
    df_data = get_df_data(df_predictions,df_trash_gps)

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

    # Close PG connection
    close_pg_connection(pg_connection)

    logger.info('############################################################')
    logger.info('################   Plastic Origin ETL End   ################')
    logger.info('############################################################')

##### Main Execution ####
# Defining parser
parser = argparse.ArgumentParser()
parser.add_argument('-c','--containername',required=True, help='container name to get blob info from and download blob from to be processed by ETL')
parser.add_argument('-b','--blobname', required=True, help='blob name to be downloaded from azure blob storage campaign0 container into /tmp')
parser.add_argument('-v','--videoname', required=True,help='video name stored locally in /tmp to apply gpx extraction process on')
parser.add_argument('-a','--aiurl', required=True,help='url endpoint where AI inference service can be reached')

# Create args parsing standard input
args = parser.parse_args()

# Run main
if __name__ == '__main__':
        main(args)