import os
import warnings

import gpxpy
import gpxpy.gpx
from azure.storage.blob import BlobClient
from tqdm import tqdm

from .ai_ops import ai_ready, get_predicted_trashs, mapLabel2TrashIdPG
from .blob_ops import list_container_blob_names, download_blob
from .gps_ops import (
    goproToGPX,
    gpx_to_gps,
    get_media_duration,
    fillGPS,
    points_to_shape,
    points_to_2154,
)
from .postgre_ops import (
    get_db_connection_string,
    open_db_connection,
    close_db_connection,
    trashGPS,
    insert_trash_to_db,
)

warnings.filterwarnings("ignore")


def process(container_name, blob_video_name):
    ######## Pipeline Step0: Get Video to predict and insert#########
    print("######## Pipeline Step0: Get Video from Azure Blob Storage #########")
    # blob storage connection string
    connection_string = os.getenv("CONN_STRING")

    # get list of blobs in container campaign0
    campaign_container_name = container_name
    blobs_campaign0 = list_container_blob_names(connection_string, campaign_container_name)

    # get infos of blob 'goproshort-480p.mov' '28022020_Boudigau_4_short.mp4'
    # blob_video_name = file_path
    # get_blob_infos(connection_string, campaign_container_name, blob_video_name)

    # download locally in /tmp blob video
    blob_client = BlobClient.from_connection_string(
        conn_str=connection_string,
        container_name=campaign_container_name,
        blob_name=blob_video_name,
    )
    download_blob(blob_client)

    ######## Pipeline Step 1bis: AI Trash prediction #########
    print("######## Pipeline Step 1bis: AI Trash prediction #########")

    isAIready = ai_ready("http://aiapisurfrider.northeurope.cloudapp.azure.com:5000")

    if isAIready:
        predicted_trashs = get_predicted_trashs(blob_video_name)
    else:
        print("Early exit of ETL workflow as AI service is not available")
        exit()

    ######## Pipeline Step 1: GPX creation ########
    print("######## Pipeline Step 1: GPX creation ########")
    video_name = "28022020_Boudigau_4.MP4"
    gpx_data = gpxpy.parse(goproToGPX(video_name))

    # GPS Points
    gpsPoints = gpx_to_gps(gpx_data)

    # Video duration
    print("\n")
    video_duration = get_media_duration("/tmp/" + video_name)
    print("Video duration in second from metadata:", video_duration)

    # GPS file duration
    timestampDelta = gpsPoints[len(gpsPoints) - 1]["Time"] - gpsPoints[0]["Time"]
    print("GPS file time coverage in second: ", timestampDelta.seconds)

    ######## Pipeline Step 2: Create gpsPointFilled ########
    print("######## Pipeline Step 2: Create gpsPointFilled ########")
    video_duration_sup = int(video_duration) + 1
    gpsPointsFilled = fillGPS(gpsPoints, video_duration_sup)

    ######## Pipeline Step 3: Transform to GPS shapePoints ########
    print("######## Pipeline Step 3: Transformation to GPS shapePoints ########")
    gpsShapePointsFilled = points_to_shape(gpsPointsFilled)

    ######## Pipeline Step 4: Transform to 2154 Geometry ########
    print("######## Pipeline Step 4: Transformation to 2154 Geometry ########")
    gps2154PointsFilled = points_to_2154(gpsShapePointsFilled)

    ######## Pipeline Step 5: Insert within PostGre ########
    print("######## Pipeline Step 5: Insert within PostGre ########")

    # Get connection string information from env variables
    pgConn_string = get_db_connection_string()
    # Open pgConnection
    pgConnection = open_db_connection(pgConn_string)
    # Create Cursor
    pgCursor = pgConnection.cursor()

    # INSERTING all detected_trash within PostGre
    list_row_id = []
    for predicted_trash in tqdm(predicted_trashs["detected_trash"]):
        try:
            # get GPS coordinate
            trash_id = predicted_trash["id"]
            trash_gps_index = trashGPS(trash_id, gps2154PointsFilled)
            trashGps2154Point = gps2154PointsFilled[trash_gps_index]
            # get TrashTypeId from AI prediction
            label = predicted_trash.get('label')
            trashType = mapLabel2TrashIdPG(label)
            # INSERT within PostGRE
            row_id = insert_trash_to_db(trashGps2154Point, trashType, pgCursor, pgConnection)
            print("prediction:", predicted_trash["id"])
            print("rowID:", row_id)
            list_row_id.append(row_id)
        except:
            print(
                "There was an issue inserting Trash id:"
                + str(predicted_trash["id"])
                + " within PostGre"
            )
    print(
        "Successfully inserted " + str(len(list_row_id)) + " Trashes within Trash table"
    )

    # Close PG connection
    close_db_connection(pgConnection)


# Execute main function
if __name__ == "__main__":
    process("campaign0", "goproshort-480p.mov")
