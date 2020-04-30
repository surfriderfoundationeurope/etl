import os
import psycopg2
import logging

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
        raise ETLError('Could not find Postgre variable in environment. ')
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
        logger.debug("Connection established")
        return conn
    except psycopg2.OperationalError as err:
        logger.error(f"Connection failed: {err}")


def close_db_connection(connection: object):
    """ Closes a connection to a PG server

    Parameters
    ----------
    connection: PostGre connection object
    """
    try:
        connection.close()
        logger.debug("PG connection closed")
    except Exception as e:
        logger.error(f"PG connection could not close successfully: {e}")


def trashGPS(trashId, gps2154Points):
    """
    trashGPS is a dummy helper function that allows to associate a GPS point to a trashId
    This function is expected to be replaced by another one, taking real trash index in video to map correct GPS point.
    Input: a trashId from AI prediction dictionnary
    Output: a list of GPS Point in 2154 geometry
    """
    length = len(gps2154Points) + 1
    gpsIndex = trashId % length
    return gpsIndex


def insert_trash_to_db(gps_row, trash_ref: str, cursor: object, connexion: object) -> str:
    """ Insert a trash in database
    
    Parameters
    ----------
    gps_row: Row of GPS data with column 'elevation' and 'geom'
    trash_ref: id of detected trash
    cursor: postgre cursor to exeecute
    connexion: PostGre connection object

    Returns
    -------
    row_id: id of row within Trash Table of the Trash which has just been inserted
    """
    timestamp = gps_row.name
    # Todo/Question: id, id_ref_campaign_fk seems to be missing
    cursor.execute(
        "INSERT INTO campaign.trash (id, id_ref_campaign_fk,the_geom, elevation, id_ref_trash_type_fk,brand_type,time ) "
        "VALUES (DEFAULT, '1faaee65-1edb-45ab-bdd4-15268fccd301',ST_SetSRID(%s::geometry,2154),%s,%s,%s,%s) RETURNING id;",
        (gps_row.geom, gps_row.elevation, trash_ref, "icetea", timestamp),
    )
    connexion.commit()
    row_id = cursor.fetchone()[0]
    return row_id
