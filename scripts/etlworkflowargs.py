# import prerequesite for blob
from azure.storage.blob import ContainerClient
from azure.storage.blob import BlobClient
from modules.blob import blob_in_container,blob_infos,download_blob
# import prerequesite for ai
import json
import requests
import logging
from modules.ai import ai_ready,get_prediction,json_prediction,get_trash_label,map_label_2_trash_id_PG
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
from modules.gps import extract_gpx_from_gopro,gps_point_list,get_media_info,get_duration,create_time,create_latitude,create_longitude,create_elevation,fill_gps,long_lat_2_shape_point,long_lat_2_shape_list,transform_geo,gps_2154
# import prerequesite from media
from modules.media import get_media_duration
# import prerequesite for postgre
import os
import psycopg2
from modules.postgre import pg_connection_string,pg_open_connection,pg_close_connection,trash_gps,trash_insert
import warnings
warnings.filterwarnings('ignore')
# import argparse to pass parameters to main function
import argparse

#### Main definition ####
def main(argv):

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
    campaign_container_name = argv.containername
    blobs_campaign0 = blob_in_container(connection_string,campaign_container_name)
    print("Blobs in container:")
    print(blobs_campaign0)

    # get infos of blob 'goproshort-480p.mov' '28022020_Boudigau_4_short.mp4'
    blob_video_name = argv.blobname   
    blob_infos(connection_string,campaign_container_name,blob_video_name)

    # download locally in /tmp blob video
    blob_video = BlobClient.from_connection_string(conn_str=connection_string,container_name=campaign_container_name, blob_name=blob_video_name)
    download_blob(blob_video)

    print('###################### Pipeline Step1bis ###################')
    print('##################### AI Trash prediction ##################')
    isAIready = ai_ready(f'{argv.aiurl}:5000')
    #logger =  logging.getLogger() #required by getPrediction()

    if isAIready == True:
        prediction = get_prediction(blob_video_name,f'{argv.aiurl}:5000')
    else:
        print("Early exit of ETL workflow as AI service is not available")
        exit()

    # cast prediction to JSON/Dictionnary format
    jsonPrediction = json_prediction(prediction)

    print('###################### Pipeline Step1 ######################')
    print('######################  GPX creation  ######################')
    video_name = argv.videoname
    before = datetime.now()
    gpx_path = extract_gpx_from_gopro(f'/tmp/{video_name}')
    after = datetime.now()
    delta = after - before
    print(delta)

    # GPX parsing
    gpx_file = open(gpx_path,'r',encoding='utf-8')
    gpx_data = gpxpy.parse(gpx_file) # data from parsed gpx file

    # GPS Points
    gpsPoints = gps_point_list(gpx_data)

    # Video duration
    print("\n")
    video_duration = get_media_duration('/tmp/'+video_name)
    print("Video duration in second from metadata:",video_duration)

    # GPS file duration
    timestampDelta = gpsPoints[len(gpsPoints)-1]['Time'] - gpsPoints[0]['Time']
    print("GPS file time coverage in second: ",timestampDelta.seconds)

    print('###################### Pipeline Step2 ######################')
    print('################## Add missing GPS points ##################')
    video_duration_sup = int(video_duration)+1
    gpsPointsFilled = fill_gps(gpsPoints,video_duration_sup)

    print('###################### Pipeline Step3 ######################')
    print('############ Transformation to GPS Shape Points ############')
    gpsShapePointsFilled = long_lat_2_shape_list(gpsPointsFilled)

    print('###################### Pipeline Step4 ######################')
    print('############## Transformation to 2154 Geometry #############')
    gps2154PointsFilled = gps_2154(gpsShapePointsFilled)

    print('###################### Pipeline Step5 ######################')
    print('################### Insert within PostGre ##################')
    
    # Get connection string information from env variables
    pgConn_string = pg_connection_string()
    # Open pgConnection
    pgConnection = pg_open_connection(pgConn_string)
    # Create Cursor
    pgCursor = pgConnection.cursor()


    # INSERTING all detected_trash within PostGre
    rowID_list = []
    for prediction in tqdm(jsonPrediction['detected_trash']):
        try: 
            # get GPS coordinate
            trashTypeId= prediction['id']
            gpsIndexId = trash_gps(trashTypeId,gps2154PointsFilled)
            trashGps2154Point = gps2154PointsFilled[gpsIndexId]
            # get TrashTypeId from AI prediction
            label = get_trash_label(prediction)
            trashType = map_label_2_trash_id_PG(label)
            # INSERT within PostGRE
            rowID = trash_insert(trashGps2154Point,trashType,pgCursor,pgConnection)
            rowID_list.append(rowID)
        except:
            print("There was an issue inserting Trash id:" + str(prediction['id']) + " within PostGre")
    print("Successfully inserted " + str(len(rowID_list)) + " Trashes within Trash table")    

    # Close PG connection
    pg_close_connection(pgConnection)

    print('############################################################')
    print('################   Plastic Origin ETL End   ################')
    print('############################################################')

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