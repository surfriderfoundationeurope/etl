import os
import psycopg2
import logging

import pandas as pd

from .exceptions import ETLError

logger = logging.getLogger()


def get_db_connection_string() -> str:
    """Compute connection string to connect to PostGre server

    Returns
    -------
    conn_string: Connection string
    """
    pgserver = os.getenv("PGSERVER")
    pgdatabase = os.getenv("PGDATABASE")
    pgusername = os.getenv("PGUSERNAME")
    pgpassword = os.getenv("PGPWD")

    if None in [pgserver, pgdatabase, pgusername, pgpassword]:
        raise ETLError("Could not find Postgre variable in environment. ")
    sslmode = "require"
    conn_string = "host={0} user={1} dbname={2} password={3} sslmode={4}".format(
        pgserver, pgusername, pgdatabase, pgpassword, sslmode
    )
    return conn_string


def open_db_connection(conn_string: str = None) -> object:
    """Create a new connection to PostGre server

    Parameters
    ----------
    conn_string: connection string

    Returns
    -------
    conn: new connection
    """
    if conn_string is None:
        conn_string = get_db_connection_string()
    try:
        conn = psycopg2.connect(conn_string)
        assert (
            conn is not None
        )  # indeed if the connection can't be established, `psycopg2.connect` returns None
        logger.debug("Connection established")
        return conn
    except psycopg2.OperationalError as err:
        logger.error(f"Connection failed: {err}")


def trashGPS(trashId, gps2154Points):
    """
    trashGPS is a dummy helper function that allows to associate a GPS point to a trashId
    This function is expected to be replaced by another one, taking real trash index in video to map correct GPS point.
    Input: a trashId from AI prediction dictionnary
    Output: a list of GPS Point in 2154 geometry
    """
    # Todo/question: correct this one
    length = len(gps2154Points) + 1
    gpsIndex = trashId % length
    return gpsIndex


def insert_trash_to_db(trash_time: pd.Timestamp, trash: pd.Series, cursor: object, connexion: object) -> str:
    """ Insert a trash in database
    
    Parameters
    ----------
    gps_row: Row of GPS data with column 'elevation' and 'geom'
    trash_ref: id of detected trash
    cursor: postgre cursor to execute
    connexion: PostGre connection object

    Returns
    -------
    row_id: id of row within Trash Table of the Trash which has just been inserted

    Examples
    ---------
    >>> trash
        longitude                                        -117.327
        latitude                                          33.1265
        elevation                                         -17.228
        id                                                      0
        label                                           fragments
        box                               [0.43, 0.44, 0.49, 0.5]
        frame                                                   2
        geom         POINT (-6843671.309553764 12301224.24713064)
        Name:           2018-01-24 19:27:58.500000, dtype: object
    >>> trash_time
        Timestamp('2018-01-24 19:27:58.500000')

    """

    trash_id = trash.get("id")
    trash_label = trash.get("label")
    trash_geom = trash.get("geom")
    trash_box = trash.get("box")
    trash_frame = trash.get("frame")
    trash_longitude = trash.get("longitude")
    trash_latitude = trash.get("latitude")
    trash_elevation = trash.get("elevation")

    # Todo/Question: id, id_ref_campaign_fk seems to be missing
    # Todo/Question;: should we insert some other data ?
    #  I suggest:
    #   - media_source,
    #   - media_id, trash_box, trash_frame : to be able to use the media image as input of TrashRoulette and eventually retrain the AI
    #   - trash_latitude, trash_longitude: just in case the transformation went wrong (+ I'm not sure it's bijective)

    # Todo/Question what is 'icetea' ?
    # Todo/Question: this function should expect a db description to be able to adapt to migrations & versions.
    cursor.execute(
        "INSERT INTO campaign.trash (id, id_ref_campaign_fk,the_geom, elevation, id_ref_trash_type_fk,brand_type,time ) "
        "VALUES (DEFAULT, '1faaee65-1edb-45ab-bdd4-15268fccd301',ST_SetSRID(%s::geometry,2154),%s,%s,%s,%s) RETURNING id;",
        (trash_geom, trash_elevation, trash_label, "icetea", trash_time),
    )
    connexion.commit()
    row_id = cursor.fetchone()[0]
    return row_id
