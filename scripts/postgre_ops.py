import psycopg2

def pgOpenConnection(conn_string):
    try:
        conn = psycopg2.connect(conn_string)
        print("Connection established")
        return conn
    except psycopg2.OperationalError as err:
        print("Connection could not established: ",err)
    #return conn

# Function to close connection to PG server
def pgCloseConnection(connection):
    try:
        connection.close()
        print("PG connection closed")
    except:
        print("PG connection could not close successfully")

# Label to TrashId PGSQL Data Model
def mapLabel2TrashIdPG(label):
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

# Dummy Function to give GPS point to Detected Trash, based on TrashId
def trashGPS(trashId,gps2154Points):
    length = len(gps2154Points)+1
    gpsIndex = trashId % length
    return gpsIndex


# INSERT REQUEST: point parameter + trashTypeId + Timestamp
def trashInsert(gps2154Point,trashTypeId,cursor,connexion):
    point = 'POINT(' + str(gps2154Point['the_geom'].coords.xy[0][0]) + ' ' + str(gps2154Point['the_geom'].coords.xy[1][0]) + ')'
    elevation = gps2154Point['Elevation']
    timestamp = gps2154Point['Time']
    cursor.execute("INSERT INTO public.trash (id, id_ref_campaign_fk,the_geom, elevation, id_ref_trash_type_fk,brand_type,time ) VALUES (DEFAULT, '003d8675-29e3-4cde-a315-095ac2ec80bc',%s,%s,%s,%s,%s) RETURNING id;", (point,elevation,trashTypeId,'icetea',timestamp))
    connexion.commit()
    row_id = cursor.fetchone()[0]
    return row_id

print("hello from postgre.py")