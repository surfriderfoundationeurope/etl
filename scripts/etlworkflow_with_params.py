import logging
import os

from azure.storage.blob import BlobClient
from dotenv import load_dotenv
from tqdm import tqdm

from utils.ai_ops import ai_ready, get_predicted_trashs, mapLabel2TrashIdPG
from utils.blob_ops import download_blob
from utils.dsp import uniform_sampling
from utils.gps_ops import (
    extract_gpx_from_gopro,
    get_media_duration,
    add_geom_to_gps_data,
    gpx_to_gps
)
from utils.postgre_ops import (
    open_db_connection,
    trashGPS,
    insert_trash_to_db,
)

logger = logging.getLogger()
# load env variable from file .env
load_dotenv()
blob_conn_string = os.getenv("CONN_STRING")
ai_url = os.getenv("AI_URL")

# warnings.filterwarnings("ignore")


media_name = 'hero6.mp4'  # "28022020_Boudigau_4.MP4" #'hero6.mp4'
local_path = '/Users/raph/Documents/SurfriderFoundation/data/samples/gopro/'  # "../goprosamples"


def etl(container_name: str = None, blob_name: str = None, media_name: str = None, local_path: str = None):
    """

    Parameters
    ----------
    container_name
    blob_name
    media_name
    local_path: if `local_path` is given, ignore container_name and `blob_name`

    Returns
    -------

    """
    if local_path is None:
        # Get media from azure blob storage
        logger.info("[Extract] Get Video from Azure Blob Storage")
        # Download locally it locally
        blob_client = BlobClient.from_connection_string(
            conn_str=blob_conn_string,
            container_name=container_name,
            blob_name=blob_name,
        )
        # Todo/question: should we check that the media has not yet been downloaded ? (eg. with a checksum if path exists)
        media_path = download_blob(blob_client=blob_client, local_path='/tmp')

    else:
        logger.info("[Extract] Get Video from Local Storage")
        media_path = os.path.join(local_path, media_name)
        # check that the file exists, else return
        if not os.path.exists(media_path):
            logger.error(f'Cannot find media {media_path} in local storage. ')
            return
    # AI Trash prediction
    logger.info("[Transform][0] Get AI trashs prediction")

    if ai_ready(ai_url):
        predicted_trashs = get_predicted_trashs(media_path=media_path, ai_url=ai_url)
    else:
        logger.error("Early exit of ETL workflow as AI service is not available")
        # return
    # Handle spatial coordinates
    logger.info("[Transform][1] Get media spatial coordinates")
    # Check if there's a GPX or XML data file with same name than the media
    base_path = os.path.splitext(media_path)[0]
    gpx_path = base_path + '.gpx'
    if os.path.exists(gpx_path):
        logger.debug('Found GPX file attached to the given media. ')
    else:
        logger.debug('Extracting GPX from Go-Pro file ')
        # Extract GPX data from media and creates a .GPX file
        # Todo: here is where we should handle different input format (binary, separate...)
        gpx_path = extract_gpx_from_gopro(media_path=media_path, format="GPX", binary=False)

    # GPS data
    gps_data = gpx_to_gps(gpx_path)

    # Video duration
    # Todo: check the paths (see todo in `download_blob` Q-> download video one by one, or ?
    video_duration = get_media_duration(media_path)
    logger.debug(f" \n Video duration in second from metadata: {video_duration}")

    # GPS file duration
    # Todo: check that video_duration and gps_duration are closed
    # gps_duration = (gps_data[-1]['time'] - gps_data[0]['time']).total_seconds()
    gps_duration = (gps_data.index[-1] - gps_data.index[0]).total_seconds()
    logger.debug(f"GPS file time coverage in second: {gps_duration}")

    delta = abs(gps_duration - video_duration)
    if delta > 2:  # more than 2 seconds of difference between video and gps duration
        logger.warning(f'{delta} seconds of difference between video and gps duration !')
    # Todo get video start recording timestamp to eventually pad the GPS data at beginning/end

    logger.debug("Resampling GPS data")
    gps_data = uniform_sampling(gps_data, sampling_rate=1,
                                interpolation_kind='linear')  # Todo @clement, what rate do we want ?

    logger.debug("Transform GPS coordinates in geometry")
    add_geom_to_gps_data(gps_data, source_epsg=4326, target_epsg=2154)

    # Insert within PostGre
    logger.info("[Load] Insert trash and coordinates to PostGre database")

    # Open pgConnection
    db_connection = open_db_connection()
    # Create Cursor
    db_cursor = db_connection.cursor()

    # INSERTING all detected_trash within PostGre
    list_row_id = []
    for predicted_trash in tqdm(predicted_trashs):
        try:

            trash_id = predicted_trash.get('id')
            trash_label = predicted_trash.get('label')
            trash_type = mapLabel2TrashIdPG(trash_label)  # Todo: get rid of this ?

            trash_gps_index = trashGPS(trash_id, gps_data)  # Todo: adapt that to new DataFrame format
            trash_coordinates = gps_data.iloc[trash_gps_index].geom

            # INSERT within PostGRE
            row_id = insert_trash_to_db(trash_coordinates, trash_type, db_cursor, db_connection)
            logger.debug(f"prediction: {trash_id} \n"
                         f"row id: {row_id}")
            list_row_id.append(row_id)
        except Exception as e:
            logger.warning(f"There was an issue inserting trash with id {trash_id} within Postgre: {e}")
    logger.info(
        f"Successfully inserted {len(list_row_id)} trashes within trash table"
    )

    # Close PG connection
    db_connection.close()


# Execute main function
if __name__ == "__main__":
    etl(media_name=media_name, local_path=local_path)
