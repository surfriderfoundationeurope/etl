import os
import psycopg2

def pgConnectionString():
    '''
    pgConnectionString function creates the connection string to connect to PostGre server
    Input: none
    Output: the connection string
    '''
    pgserver = os.getenv("PGSERVER")
    pgdatabase = os.getenv("PGDATABASE")
    pgusername = os.getenv("PGUSERNAME")
    pgpassword = os.getenv("PGPWD")
    sslmode = "require"
    conn_string = "host={0} user={1} dbname={2} password={3} sslmode={4}".format(pgserver, pgusername, pgdatabase, pgpassword, sslmode)
    return conn_string

def pgOpenConnection(conn_string):
    '''
    pgOpenConnection function open a connection to PostGre server
    Input: a connection string formated for PG server, from pgConnectionString output
    Output: in case successful, a postgre connection object
    '''
    try:
        conn = psycopg2.connect(conn_string)
        print("Connection established")
        return conn
    except psycopg2.OperationalError as err:
        print("Connection could not established: ",err)


def pgCloseConnection(connection):
    '''
    pgCloseConnection function closes a connection to a PG server
    Input: a PostGre connection object, output from pgOpenConnection
    Output: None
    '''
    try:
        connection.close()
        print("PG connection closed")
    except:
        print("PG connection could not close successfully")


def mapLabel2TrashIdPG(label):
    '''
    mapLabel2TrashIdPG function is a different mapping between a predicted label by AI and TrashId as defined within TrashType table
    Input: a label predicted by AI
    Output: a TrashId as defined in TrashType table
    '''
    switcher = { 
        "others":"1", #"autre dechet" in PG Data Model mapped to IA "others" label
        "dechet agricole":"2",
        "bottles":"3", #"bouteille boisson" in PG Data Model mapped to IA "bottles" label
        "fragments":"4",#"industriel ou construction in PG Data Model mapped to IA "fragments" label
        "peche et chasse":"5",
        "emballage alimentaire":"6",
        "objet vie courante":"7",
        "autres dechets +10":"8"
    } 
    return switcher.get(label, "nothing")


def trashGPS(trashId,gps2154Points):
    '''
    trashGPS is a dummy helper function that allows to associate a GPS point to a trashId
    This function is expected to be replaced by another one, taking real trash index in video to map correct GPS point.
    Input: a trashId from AI prediction dictionnary
    Output: a list of GPS Point in 2154 geometry
    '''
    length = len(gps2154Points)+1
    gpsIndex = trashId % length
    return gpsIndex


def trashInsert(gps2154Point,trashTypeId,cursor,connexion):
    '''
    trashInsert function is the actual INSERT of a Trash detected by AI within PostGre Trash Table
    Input: a gps2154Point, a TrashTypeId, a postgre cursor, a postgre connection
    Output: the row_id within Trash Table of the Trash which has just been inserted
    '''
    point = gps2154Point['the_geom'].wkt
    elevation = gps2154Point['Elevation']
    timestamp = gps2154Point['Time']
    cursor.execute("INSERT INTO campaign.trash (id, id_ref_campaign_fk,the_geom, elevation, id_ref_trash_type_fk,brand_type,time ) VALUES (DEFAULT, 'ff7c7426-d8f5-4173-9b2a-129f01f720f1',ST_SetSRID(%s::geometry,2154),%s,%s,%s,%s) RETURNING id;", (point,elevation,trashTypeId,'icetea',timestamp))
    connexion.commit()
    row_id = cursor.fetchone()[0]
    return row_id

print("Successful import of postgre_ops")