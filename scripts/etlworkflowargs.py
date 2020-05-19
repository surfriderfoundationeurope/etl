# import prerequesite for blob
from azure.storage.blob import ContainerClient
from azure.storage.blob import BlobClient
from modules.blob import blob_in_container,blob_infos,download_blob
# import prerequesite for ai
import json
import requests
import logging
from modules.ai import ai_ready,get_prediction,json_prediction,get_trash_label,map_label_2_trash_id_PG,get_trash_time_index,get_trash_time_stamp
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
from modules.gps import extract_gpx_from_gopro,gps_point_list,create_time,create_latitude,create_longitude,create_elevation,fill_gps,long_lat_2_shape_point,long_lat_2_shape_list,transform_geo,gps_2154,parse_gpx
# import prerequesite from media
from modules.media import get_media_duration,get_media_fps
# import prerequesite for postgre
import os
import psycopg2
from modules.postgre import pg_connection_string,pg_open_connection,pg_close_connection,trash_gps,trash_insert
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
    # Download Blob video
    connection_string = os.getenv("CONN_STRING")
    campaign_container_name = argv.containername
    blob_video_name = argv.blobname   
    blob_video = BlobClient.from_connection_string(conn_str=connection_string,container_name=campaign_container_name, blob_name=blob_video_name)
    download_blob(blob_video)

    logger.info('###################### Pipeline Step1bis ###################')
    logger.info('##################### AI Trash prediction ##################')
    isAIready = ai_ready(f'{argv.aiurl}:5000')
    #logger =  logging.getLogger() #required by getPrediction()

    '''
    if isAIready == True:
        prediction = get_prediction(blob_video_name,f'{argv.aiurl}:5000')
    else:
        logger.info("Early exit of ETL workflow as AI service is not available")
        exit()
  
    # cast prediction to JSON/Dictionnary format
    jsonPrediction = json_prediction(prediction)
    '''
    # optionnal jsonPrediction from local file
    
    with open('../data/prediction.json') as json_file:
        jsonPrediction = json.load(json_file)
    

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
    gps_points = gps_point_list(gpx_data)

    # Video duration
    logger.info("\n")
    video_duration = get_media_duration(f'/tmp/{video_name}')
    logger.info(f'Video duration in second from metadata:{video_duration}')
    media_fps = get_media_fps(f'/tmp/{video_name}')

    # GPS file duration
    timestampDelta = gps_points[len(gps_points)-1]['Time'] - gps_points[0]['Time']
    logger.info(f'GPS file time coverage in second:{timestampDelta.seconds}')

    logger.info('###################### Pipeline Step2 ######################')
    logger.info('################## Add missing GPS points ##################')
    video_duration_sup = int(video_duration)+1
    gps_points_filled = fill_gps(gps_points,video_duration_sup)

    logger.info('###################### Pipeline Step3 ######################')
    logger.info('################### Insert within PostGre ##################')
    
    # Get connection string information from env variables
    pgConn_string = pg_connection_string()
    # Open pgConnection
    pgConnection = pg_open_connection(pgConn_string)
    # Create Cursor
    pgCursor = pgConnection.cursor()


    # INSERTING all detected_trash within PostGre
    row_id_list = []
    for prediction in tqdm(jsonPrediction['detected_trash']):
        try:    
            # get trash_gps from gps module
            timeindex = get_trash_time_index(prediction)
            timestamp = get_trash_time_stamp(timeindex,media_fps)
            trash_gps = gps_points[timestamp]
            shape_trash_gps = long_lat_2_shape_point(trash_gps)
            geo_2154 = transform_geo(shape_trash_gps)
            geo_2154_trash_gps = {'Time': shape_trash_gps['Time'], 'the_geom': geo_2154,'Latitude':shape_trash_gps['Latitude'],'Longitude':shape_trash_gps['Longitude'], 'Elevation': shape_trash_gps['Elevation']}
            # get trash_type from ai module
            label = get_trash_label(prediction)
            trash_type = map_label_2_trash_id_PG(label)
            # insert trash from postgre module
            row_id = trash_insert(geo_2154_trash_gps,trash_type,pgCursor,pgConnection)
            row_id_list.append(row_id)
        except:
            prediction_id = prediction['id']
            logger.error(f'There was an issue inserting Trash id: {prediction_id} within PostGre')
            logger.error("Early exit of ETL workflow as PG INSERT failed")
            exit()
    logger.info(f'Successfully inserted {str(len(row_id_list))} Trashes within Trash table')    

    # Close PG connection
    pg_close_connection(pgConnection)

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