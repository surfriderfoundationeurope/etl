# import prerequesite for blob_ops
from azure.storage.blob import ContainerClient
from azure.storage.blob import BlobClient
from blob_ops import blobInContainer,blobInfos,downloadBlob
# import prerequesite for ai_ops
import json
import requests
import logging
from ai_ops import AIready,getPrediction,jsonPrediction,getTrashLabel,mapLabel2TrashIdPG
# import prerequesite for gps_ops
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
from gps_ops import goproToGPX,gpsPointList,getMediaInfo,getDuration,createTime,createLatitude,createLongitude,createElevation,fillGPS,longLat2shapePoint,longLat2shapeList,geometryTransfo,gps2154
# import prerequesite for postgre_ops
import os
import psycopg2
from postgre_ops import pgConnectionString,pgOpenConnection,pgCloseConnection,trashGPS,trashInsert
import warnings
warnings.filterwarnings('ignore')

def main():

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
    campaign_container_name = 'campaign0'
    blobs_campaign0 = blobInContainer(connection_string,campaign_container_name)

    # get infos of blob 'goproshort-480p.mov' '28022020_Boudigau_4_short.mp4'
    blob_video_name = 'goproshort-480p.mov'   
    blobInfos(connection_string,campaign_container_name,blob_video_name)

    # download locally in /tmp blob video
    blob_video = BlobClient.from_connection_string(conn_str=connection_string,container_name=campaign_container_name, blob_name=blob_video_name)
    downloadBlob(blob_video)

    print('###################### Pipeline Step1bis ###################')
    print('##################### AI Trash prediction ##################')

    isAIready = AIready('http://aiapisurfrider.northeurope.cloudapp.azure.com:5000')
    logger =  logging.getLogger() #required by getPrediction()

    if isAIready == True:
        prediction = getPrediction(blob_video_name)
    else:
        print("Early exit of ETL workflow as AI service is not available")
        exit()

    # cast prediction to JSON/Dictionnary format
    json_prediction = jsonPrediction(prediction)

    print('###################### Pipeline Step1 ######################')
    print('######################  GPX creation  ######################')
    video_name = '28022020_Boudigau_4.MP4'
    gpx_path = goproToGPX(video_name)

    # GPX parsing
    gpx_file = open(gpx_path,'r',encoding='utf-8')
    gpx_data = gpxpy.parse(gpx_file) # data from parsed gpx file

    # GPS Points
    gpsPoints = gpsPointList(gpx_data)

    # Video duration
    print("\n")
    video_duration = getDuration('/tmp/'+video_name)
    print("Video duration in second from metadata:",video_duration)

    # GPS file duration
    timestampDelta = gpsPoints[len(gpsPoints)-1]['Time'] - gpsPoints[0]['Time']

    print("GPS file time coverage in second: ",timestampDelta.seconds)
    print('###################### Pipeline Step2 ######################')
    print('################## Add missing GPS points ##################')
    video_duration_sup = int(video_duration)+1
    gpsPointsFilled = fillGPS(gpsPoints,video_duration_sup)

    print('###################### Pipeline Step3 ######################')
    print('############ Transformation to GPS Shape Points ############')
    gpsShapePointsFilled = longLat2shapeList(gpsPointsFilled)

    print('###################### Pipeline Step4 ######################')
    print('############## Transformation to 2154 Geometry #############')
    gps2154PointsFilled = gps2154(gpsShapePointsFilled)

    print('###################### Pipeline Step5 ######################')
    print('################### Insert within PostGre ##################')


    # Get connection string information from env variables
    pgConn_string = pgConnectionString()
    # Open pgConnection
    pgConnection = pgOpenConnection(pgConn_string)
    # Create Cursor
    pgCursor = pgConnection.cursor()


    # INSERTING all detected_trash within PostGre
    rowID_list = []
    for prediction in tqdm(json_prediction['detected_trash']):
        try: 
            # get GPS coordinate
            trashTypeId= prediction['id']
            gpsIndexId = trashGPS(trashTypeId,gps2154PointsFilled)
            trashGps2154Point = gps2154PointsFilled[gpsIndexId]
            # get TrashTypeId from AI prediction
            label = getTrashLabel(prediction)
            trashType = mapLabel2TrashIdPG(label)
            # INSERT within PostGRE
            rowID = trashInsert(trashGps2154Point,trashType,pgCursor,pgConnection)
            rowID_list.append(rowID)
        except:
            print("There was an issue inserting Trash id:" + str(prediction['id']) + " within PostGre")
    print("Successfully inserted " + str(len(rowID_list)) + " Trashes within Trash table")    

    # Close PG connection
    pgCloseConnection(pgConnection)

    print('############################################################')
    print('################   Plastic Origin ETL End   ################')
    print('############################################################')


# Execute main function
if __name__ == '__main__':
    main()