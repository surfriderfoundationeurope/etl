import logging
import os

from azure.storage.blob import BlobClient
from dotenv import load_dotenv
import pandas as pd

from etl.utils.ai import ai_ready, get_ai_prediction, prediction_to_dataframe
from etl.utils.blob import download_blob
from etl.utils.database import (
    open_db_connection,
    insert_trash_to_db,
)
from etl.utils.dsp import custom_sampling
from etl.utils.exceptions import ETLError
from etl.utils.gps import (
    extract_gpx_from_gopro,
    get_media_duration,
    add_geom_to_gps_data,
    gpx_tracks_to_gps,
    open_gpx_file,
    gpx_waypoints_to_gps,
)
from etl.utils.media import infer_media_source

logger = logging.getLogger()
# load env variable from file .env
load_dotenv()
blob_conn_string = os.getenv("CONN_STRING")


def run_etl(
        container_name: str = None,
        blob_name: str = None,
        media_name: str = None,
        data_dir: str = None,
        temp_dir: str = "/tmp",
        data_source: str = "azure",
        ai_url: str = None,
):
    """ ETL: Extract trash and their associated coordinates from a media and insert it to a database

    Parameters
    ----------
    container_name
    blob_name
    media_name
    data_dir: if `data_dir` is given, ignore container_name and `blob_name`
    temp_dir:

    Returns
    -------

    """

    if ai_url is None:
        ai_url = os.getenv("AI_URL")

    if data_source == "azure":
        # Get media from azure blob storage
        logger.info("[Extract] Get Video from Azure Blob Storage")
        # Download locally it locally
        blob_client = BlobClient.from_connection_string(
            conn_str=blob_conn_string,
            container_name=container_name,
            blob_name=blob_name,
        )
        # Todo/question: should we check that the media has not yet been downloaded ? (eg. with a checksum if path exists)
        media_path = download_blob(blob_client=blob_client, local_path=temp_dir)

    elif data_source == "local":
        if data_dir is None:
            raise ValueError("`data_dir` is required when mode `data_source` is local")
        logger.info("[Extract] Get Video from Local Storage")
        media_path = os.path.join(data_dir, media_name)
        # check that the file exists, else return
        if not os.path.exists(media_path):
            raise ETLError(f"Cannot find media {media_path} in local storage. ")
    else:
        raise ValueError(f"Unkonwn data source {data_source}")

    # Infer media source : 'gopro', 'smartphone_photo', 'smartphone_video' or 'osm_tracker'
    media_source = infer_media_source(media_path)

    # Handle spatial coordinates
    logger.info("[Transform] Get media spatial coordinates")
    # Check if there's a GPX or XML data file with same name than the media

    base_path = os.path.splitext(media_path)[0]
    gpx_path = base_path + ".gpx"
    if media_source == "gopro" and not os.path.exists(gpx_path):
        logger.debug("Extracting GPX from Go-Pro file ")
        # Extract GPX data from media and creates a .GPX file
        # Todo: here is where we should handle different input format (binary, separate...)
        gpx_path = extract_gpx_from_gopro(
            media_path=media_path, format="GPX", binary=False
        )

    # At this point, we are sure that there is a GPX file
    gpx_data = open_gpx_file(gpx_path)
    # GPS data
    if media_source == "osm_tracker":
        # no need for AI, trash are givene in waypoints
        gps_data = gpx_waypoints_to_gps(gpx_data)
    else:
        gps_data = gpx_tracks_to_gps(gpx_data)
        # Video duration
        video_duration = get_media_duration(media_path)
        logger.debug(f" \n Video duration in second from metadata: {video_duration}")

        # GPS file duration
        gps_duration = (gps_data.index[-1] - gps_data.index[0]).total_seconds()
        logger.debug(f"GPS file time coverage in second: {gps_duration}")

        # Sanity check: duration should be closed
        delta = abs(gps_duration - video_duration)
        if (delta > 2):  # more than 2 seconds of difference between video and gps duration
            logger.warning(
                f"{delta} seconds of difference between video and gps duration !"
            )
        # Todo get video start recording timestamp to eventually pad the GPS data at beginning/end

        logger.debug("Resampling GPS data")

    # At this point, we have GPS data with columns ['longitude', 'latitude', 'geom']
    # + eventually 'trash_label', and 'elevation'

    # If 'trash_label' not in data, call the AI to detect trashes
    logger.info("[Transform] Get AI trashs prediction")

    if media_source == "osm_tracker":
        # no need to call AI, trashes label are already in the DataFrame
        data = gps_data
    else:
        if ai_ready(ai_url):
            ai_prediction = get_ai_prediction(media_path=media_path, ai_url=ai_url)
        else:
            logger.error("Early exit of ETL workflow as AI service is not available")
            # todo: remove these lines, for devel purpose (fake IA answer)
            import json

            with open("data/ia_response/trashes.json") as f:
                ai_prediction = json.load(f)
        trashes_data = prediction_to_dataframe(ai_prediction, start=gps_data.index[0])
        gps_data = custom_sampling(
            gps_data, output_index=trashes_data.index, interpolation_kind="linear"
        )
        data = pd.concat([gps_data, trashes_data], axis=1)

    logger.debug("Transform GPS coordinates in geometry")
    add_geom_to_gps_data(
        data, source_epsg=4326, target_epsg=2154
    )  # NB: we add geom data at this point, so that we estimate them only for trash rows (ie. save time)

    # Insert within PostGre
    logger.info("[Load] Insert trash and coordinates to PostGre database")

    # Open pgConnection
    db_connection = open_db_connection()
    # Create Cursor
    db_cursor = db_connection.cursor()

    # INSERTING all detected_trash within PostGre
    list_row_id = []
    for trash_time, trash in data.iterrows():
        try:
            # INSERT within PostGre database
            row_id = insert_trash_to_db(trash_time, trash, db_cursor, db_connection)
            logger.debug(f"prediction: {trash} \n" f"row id: {row_id}")
            list_row_id.append(row_id)
        except Exception as e:
            logger.warning(
                f"There was an issue inserting trash {trash} within Postgre: {e}"
            )
    logger.info(f"Successfully inserted {len(list_row_id)} trashes within trash table")

    # Close PG connection
    db_connection.close()
    logger.info('ETL ran successfully !')
