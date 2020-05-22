import os
import psycopg2
import pandas as pd
from .exceptions import ETLError

#https://pynative.com/psycopg2-python-postgresql-connection-pooling/

def get_pg_connection_string()->str:
    """Get connection string to connect to PostGre server

    Returns:
        conn_string -- pg connection string
    """
    pgserver = os.getenv("PGSERVER")
    pgdatabase = os.getenv("PGDATABASE")
    pgusername = os.getenv("PGUSERNAME")
    pgpassword = os.getenv("PGPWD")
    if None in [pgserver, pgdatabase, pgusername, pgpassword]:
        raise ETLError("Could not find Postgre variable in environment. ")
    sslmode = "require"
    conn_string = "host={0} user={1} dbname={2} password={3} sslmode={4}".format(pgserver, pgusername, pgdatabase, pgpassword, sslmode)
    return conn_string

def open_pg_connection(conn_string:str)->object:
    """Open connection to PostGre server

    Arguments:
        conn_string {str} -- the postgre connection string

    Returns:
        conn -- a postgre connection as a psycopg2 object
    """
    try:
        conn = psycopg2.connect(conn_string)
        print("Connection established")
        return conn
    except psycopg2.OperationalError as err:
        print("Connection could not established: ",err)


def close_pg_connection(connection:str):
    """Close postgre server connection

    Arguments:
        connection {str} -- a postgre server connection
    """
    try:
        connection.close()
        print("PG connection closed")
    except:
        print("PG connection could not close successfully")


def get_df_data(df_predictions:pd.DataFrame,df_trash_gps:pd.DataFrame)->pd.Dataframe:
    """Get Data to be inserted within PostGre DB as a Dataframe

    Arguments:
        df_predictions {pd.DataFrame} -- the AI prediction as a Dataframe
        df_trash_gps {pd.DataFrame} -- the gps coordinate of all trash detected by AI as a Dataframe

    Returns:
        pdf_data -- Data to be inserted within PostGre DB
    """
    df_data = pd.concat([df_predictions,df_trash_gps],axis=1)
    return df_data


def insert_trash(gps_2154_point:dict,trash_type_id:int,cursor:object,connection:object):
    """Insert trash within PostGre Trash Table within Campaign schema

    Arguments:
        gps_2154_point {dict} -- the gps data associated with a trash
        trash_type_id {int} -- the trash type id as defined within Trash table
        cursor {object} -- the postgre cursor object created from connection
        connection {object} -- the postgre connection object

    Returns:
        row_id -- the new id of the row created for the trash within Trash table
    """
    point = gps_2154_point['the_geom'].wkt
    elevation = gps_2154_point['Elevation']
    timestamp = gps_2154_point['Time']
    longitude = gps_2154_point['Longitude']
    latitude = gps_2154_point['Latitude']
    cursor.execute("INSERT INTO campaign.trash (id, id_ref_campaign_fk,the_geom, elevation, id_ref_trash_type_fk,brand_type,time,lon,lat ) VALUES (DEFAULT, '6b5c65c4-238b-4d8b-b0c3-a97f262038fe',ST_SetSRID(%s::geometry,2154),%s,%s,%s,%s,%s,%s) RETURNING id;", (point,elevation,trash_type_id,'coca',timestamp,longitude,latitude))
    connection.commit()
    row_id = cursor.fetchone()[0]
    return row_id
