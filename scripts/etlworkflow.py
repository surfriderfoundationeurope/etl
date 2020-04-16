# import for ai_ops
import json
import subprocess
import requests
from ai_ops import isAIready,getPrediction,jsonPrediction,getTrashLabel,mapLabel2TrashId

# import for blob_ops
from azure.storage.blob import ContainerClient
from azure.storage.blob import BlobClient
from blob_ops import blobInContainer,blobInfos,downloadBlob

# import for gps_ops
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

# import for postgre_ops
import psycopg2
from postgre_ops import pgOpenConnection,pgCloseConnection,mapLabel2TrashIdPG,trashGPS,trashInsert
# import for main
import os
import warnings
warnings.filterwarnings('ignore')

def main():

    ######## Pipeline Step0: Get Video to predict and insert#########
    print('######## Pipeline Step0: Get Video from Azure Blob Storage #########')
    # blob storage connection string
    connection_string = os.getenv("CONN_STRING")

    # get list of blobs in container campaign0
    campaign_container_name = 'campaign0'
    blobs_campaign0 = blobInContainer(connection_string,campaign_container_name)

    # get infos of blob 'goproshort-480p.mov' 
    blob_video_name = '28022020_Boudigau_4_short.mp4'   
    blobInfos(connection_string,campaign_container_name,blob_video_name)

    # download locally in /tmp blob video
    blob_video0 = BlobClient.from_connection_string(conn_str=connection_string,container_name=campaign_container_name, blob_name=blob_video_name)
    downloadBlob(blob_video0)

    ######## Pipeline Step 1bis: AI Trash prediction #########
    print('######## Pipeline Step 1bis: AI Trash prediction #########')
    isAIready('http://aiapisurfrider.northeurope.cloudapp.azure.com:5000')
    # get predictions from AI on goproshort-480p.mov
    prediction = getPrediction(blob_video_name)

    # cast prediction to JSON/Dictionnary format
    json_prediction = jsonPrediction(prediction)
    json_prediction

    ######## Pipeline Step 1: GPX creation ########
    print('######## Pipeline Step 1: GPX creation ########')
    video_name = '28022020_Boudigau_4.MP4'
    gpx_path = goproToGPX(video_name)
    gpx_path

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

    ######## Pipeline Step 2: Create gpsPointFilled ########
    print('######## Pipeline Step 2: Create gpsPointFilled ########')
    video_duration_sup = int(video_duration)+1
    gpsPointsFilled = fillGPS(gpsPoints,video_duration_sup)

    ######## Pipeline Step 3: GPS shapePoints ########
    print('######## Pipeline Step 3: GPS shapePoints ########')
    gpsShapePointsFilled = longLat2shapeList(gpsPointsFilled)

    ######## Pipeline Step 4: 2154 geometry conversion ########
    print('######## Pipeline Step 4: 2154 Geometry conversion ########')
    gps2154PointsFilled = gps2154(gpsShapePointsFilled)

    ######## Pipeline Step 5: PostGre INSERT ########
    print('######## Pipeline Step 5: PostGre INSERT ########')
    # Postgre connection pre-requesite
    # Update connection string information from env variables
    pgserver = os.getenv("PGSERVER")
    pgdatabase = os.getenv("PGDATABASE")
    pgusername = os.getenv("PGUSERNAME")
    pgpassword = os.getenv("PGPWD")
    sslmode = "require"

    # Open pgConnection, create cursor
    conn_string = "host={0} user={1} dbname={2} password={3} sslmode={4}".format(pgserver, pgusername, pgdatabase, pgpassword, sslmode)
    pgconnection = pgOpenConnection(conn_string)
    cursor = pgconnection.cursor()


    # INSERTING all detected_trash within PostGre
    rowID_list = []
    for prediction in tqdm(json_prediction['detected_trash']):
        try: 
            # get GPS coordinate
            trashTypeId= prediction['id']
            gpsIndexId = trashGPS(trashTypeId,gps2154PointsFilled)
            gpsTrashTypeId = gps2154PointsFilled[gpsIndexId]
            # get TrashTypeId from AI prediction
            label = getTrashLabel(prediction)
            trashType = mapLabel2TrashIdPG(label)
            # INSERT within PostGRE
            rowID = trashInsert(gpsTrashTypeId,trashType,cursor,pgconnection)
            print("prediction:",prediction['id'])
            print("rowID:",rowID)
            rowID_list.append(rowID)
        except:
            print("There was an issue inserting Trash id:" + str(prediction['id']) + " within PostGre")
    print("Successfully inserted " + str(len(rowID_list)) + " Trashes within Trash table")    

    # Close PG connection
    pgCloseConnection(pgconnection)

# Execute main function
if __name__ == '__main__':
    main()