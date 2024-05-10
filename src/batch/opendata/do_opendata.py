# Pre-requesite import
import argparse
import psycopg2
import warnings
import logging
import os
import pandas as pd
from tqdm import tqdm

# Settings
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Get Environment variable
connection_string = os.getenv("CONN_STRING")
pgserver = os.getenv("PGSERVER")
pgdatabase = os.getenv("PGDATABASE")
pgusername = os.getenv("PGUSERNAME")
pgpassword = os.getenv("PGPWD")


# POSTGRE HELPER FUNCTIONS
class ETLError(Exception):
    """Base exception for all ETL-related exceptions"""

    pass

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
        #logger.info("Connection established")
        return conn
    except psycopg2.OperationalError as err:
        logger.error(f'Connection could not established: {err}')


def close_pg_connection(connection:str):
    """Close postgre server connection
    Arguments:
        connection {str} -- a postgre server connection
    """
    try:
        connection.close()
        logger.info("PG connection closed")
    except:
        logger.error("PG connection could not close successfully")


# EXTRACT HELPER FUNCTIONS

def select_yearly_bi_campaign(cursor:object,connection:object,year:int)->dict:
    """Select campaign data
    Args:
        cursor {object} -- the postgre cursor object created from connection
        connection {object} -- the postgre connection object

    Returns:
        media_info: dictionnary of media id, campaign id, media name
    """
    cursor.execute(f"SELECT * FROM bi.campaign where '{year-1}-12-31' < DATE(start_date) and DATE(start_date) <= '{year}-12-31'")
    connection.commit()
    query_result = list(cursor.fetchall()) # cast tuple to list
    return query_result


def select_bi_campaign(cursor:object,connection:object,campaign_id)->dict:
    """Select campaign data
    Args:
        cursor {object} -- the postgre cursor object created from connection
        connection {object} -- the postgre connection object
    Returns:
        media_info: dictionnary of media id, campaign id, media name
    """

    cursor.execute("SELECT * FROM bi.campaign WHERE id = %s",(campaign_id,))
    connection.commit()
    query_result = list(cursor.fetchone()) # cast tuple to list
    return query_result
    

def select_bi_trash(cursor:object,connection:object,campaign_id)->dict:
    """Select bi trash data
    Args:
        cursor {object} -- the postgre cursor object created from connection
        connection {object} -- the postgre connection object
    Returns:
        media_info: dictionnary of media id, campaign id, media name
    """

    cursor.execute("SELECT * FROM bi.trash WHERE id_ref_campaign_fk = %s",(campaign_id,))
    connection.commit()
    query_result = list(cursor.fetchall()) # cast tuple to list
    return query_result


def select_bi_river(cursor:object,connection:object,campaign_id)->dict:
    """Select campaign data
    Args:
        cursor {object} -- the postgre cursor object created from connection
        connection {object} -- the postgre connection object
    Returns:
        media_info: dictionnary of media id, campaign id, media name
    """

    cursor.execute("SELECT * FROM bi.campaign_river WHERE id_ref_campaign_fk = %s",(campaign_id,))
    connection.commit()
    query_result = list(cursor.fetchone()) # cast tuple to list
    return query_result
    

def select_bi_river_name(cursor:object,connection:object,river_id)->dict:
    """Select campaign data
    Args:
        cursor {object} -- the postgre cursor object created from connection
        connection {object} -- the postgre connection object
    Returns:
        media_info: dictionnary of media id, campaign id, media name
    """

    cursor.execute("SELECT * FROM bi.river WHERE id = %s",(river_id,))
    connection.commit()
    query_result = list(cursor.fetchone()) # cast tuple to list
    return query_result



# TRANSFORM HELPER FUNCTIONS

# function to get campaign data
def prepare_campaign_data(bi_campaign):
  ai_driven = bi_campaign[2]

  if ai_driven is True:
    tracking_mode='ai'
  else:
    tracking_mode='manual'

  campaign_data = {
    'campaign_id':bi_campaign[0],
    'move':bi_campaign[1],
    'date':bi_campaign[7],
    'bank':bi_campaign[5],
    'tracking_mode':tracking_mode,
    #'distance':bi_campaign[16],
    }

  return campaign_data

# function to map trash_id to label
def map_trash_id_to_label(trash_id:int)->str:
    """Map label of a trash to equivalent ID within PostGre server

    Arguments:
        label {str} -- the label of the trash

    Returns:
        id_PG -- the equivalent id within PG Trash table of trash label
    """
    switcher = { 
        1:"AutoFragment",
        2:"AutoInsulating",
        3:"AutoBottleShaped",
        4:"AutoCanShaped",
        5:"AutoDrum",
        6:"AutoOtherPackaging", 
        7:"AutoTire",
        8:"AutoFishingNet", 
        9:"AutoEasilynamable",
        10:"AutoUnclear",
        11:"Fragment", 
        12:"AgriculturalFoodWaste",
        13:"Bottles", 
        14:"Industrials",
        15:"FishHunting",
        16:"FoodPackage",
        17:"HouseholdItems",
        18:"Fragment10",
        19:"Trash",
        20:"BulkyTrash",
        21:"AccumulationZone"
    }
    trash_name =  switcher.get(trash_id, "1")
    return trash_name


# function to prepare trash data from bi_trash_campaign
def prepare_trash_data(bi_trash_campaign):
  trash_data = {
  'trash_type': map_trash_id_to_label(bi_trash_campaign[4]),
  'lat':bi_trash_campaign[9],
  'lon':bi_trash_campaign[10],
  'municipality':bi_trash_campaign[11],
  'department':bi_trash_campaign[13],
  'state':bi_trash_campaign[16],
  'country':bi_trash_campaign[18]
  }
  return trash_data


# function to prepare river data and handle river error
def prepare_river_data(cursor,connection,campaign):
  river = True
  
  try:
    bi_river_campaign = select_bi_river(cursor,connection,campaign)
  except (TypeError):
    #logger.error(f"It's likely that campaign {campaign} does not have a river associated. Failed getting river id, river will be unknown.")
    river = False
  try: 
    bi_river_name_campaign = select_bi_river_name(cursor,connection,bi_river_campaign[6])
  except (NameError):
    #logger.error(f"It's likely that campaign {campaign} does not have a river name associated with river id. Failed getting river name, river will be unknown.")
    river = False

  if river == True:
    campaign_river_data = {'river_name':bi_river_name_campaign[1]}
  else:
    campaign_river_data = {'river_name':'unknown river'}

  return campaign_river_data

# function to create the opendata dico for a given campaign
def get_campaign_trash_river_data(campaign_data,campaign_trash_data,campaign_river_data):
  trash_river_data_dico = {}
  trash_river_data_dico.update(campaign_data)
  trash_river_data_dico.update(campaign_trash_data)
  trash_river_data_dico.update(campaign_river_data)
  return trash_river_data_dico

# update unwanted subcategories for locomotion
def update_locomotion(locomotion):
    kayak_list = ["sup", "stand up paddle", "stand-up paddle board", "Rafting", "rafting", "raft", "purogue", "pirogye", "pirogue", "kayak"]
    walk_list = ["foot", "walk", "a pied"]
    if locomotion in kayak_list :
      new_locomotion = "kayak"
    elif locomotion in walk_list:
       new_locomotion = "walk"
    else:
       new_locomotion = 'other'
      
    return new_locomotion



# main function to create OPEN DATA
def main(argv):
    # init variables from argparse
    year = int(argv.year)
    country = argv.country

    # Init connection to DB
    pg_conn_string = get_pg_connection_string()
    pg_connection = open_pg_connection(pg_conn_string)
    pg_cursor = pg_connection.cursor()


    logger.info(f'Getting started Open Data creation.')    
    # Get list of campaigns for specified year
    bi_campaigns_year = select_yearly_bi_campaign(pg_cursor,pg_connection,year)
    columns=['id','locomotion','isaidriven','remark','id_ref_user_fk','riverside','id_ref_model_fk','start_date','end_date','start_point','end_point','avg_speed','duration','trash_count','trash_per_km','createdon','distance','the_geom']
    bi_campaigns_year_df = pd.DataFrame(bi_campaigns_year,columns=columns)

    # Set list of campaigns for specified year
    campaign_list = list(bi_campaigns_year_df['id'])
    dfs_list = [] # the list of each campaign data_df

    # Iterate over all campaigns for specified year
    for campaign in tqdm(campaign_list):

        # PG connection
        pg_conn_string = get_pg_connection_string()
        pg_connection = open_pg_connection(pg_conn_string)
        pg_cursor = pg_connection.cursor()

        # Extract Data
        bi_campaign = select_bi_campaign(pg_cursor,pg_connection,campaign)
        bi_trash_campaign = select_bi_trash(pg_cursor,pg_connection,campaign)

        # Transform Data
        campaign_data = prepare_campaign_data(bi_campaign)
        campaign_river_data = prepare_river_data(pg_cursor,pg_connection,campaign)    

        bi_trash_campaign_length = len(bi_trash_campaign)
        if bi_trash_campaign_length > 0:
            all_data_dico_list = []
            for trash_data in bi_trash_campaign:
                prepared_trash_data = prepare_trash_data(trash_data)
                trash_river_data = get_campaign_trash_river_data(campaign_data,prepared_trash_data,campaign_river_data)
                all_data_dico_list.append(trash_river_data)
            all_data_df = pd.DataFrame(all_data_dico_list)
            #logger.info(f"Data has been created for campaign {campaign}.")

        else:
            #logger.info(f"No data has been created for {campaign}. The length of bi_trash_campaign for campaign is {bi_trash_campaign_length}.")
            all_data_df = None
        
        dfs_list.append(all_data_df)

    # Concatenate data of all campaigns
    df0 = pd.DataFrame()
    if len(dfs_list) > 1: 
        for df in dfs_list[1:]:
            all_data_yearly = pd.concat([df0,df],axis=0,ignore_index=True)
            df0 = all_data_yearly
    else: 
        all_data_yearly = df0

    all_data_yearly['move'] = all_data_yearly['move'].apply(lambda x: update_locomotion(x))


    if country == 'france':
        # Filtering France only data
        france_all_data_yearly = all_data_yearly[all_data_yearly['country'] == 'France']
        france_with_known_river_all_data_yearly = france_all_data_yearly[france_all_data_yearly['river_name'] != 'unknown river']
        france_with_unknown_river_all_data_yearly = france_all_data_yearly[france_all_data_yearly['river_name'] == 'unknown river']
        all_data_yearly = france_with_known_river_all_data_yearly
        

    # Load yearly Data to CSV file
    if all_data_yearly is not None:
        if country == 'france':
            opendata_filename = f'open_data_{year}_fr.csv'
        elif country == 'all':
            opendata_filename = f'open_data_{year}_all.csv'
        with open(opendata_filename,'w') as f:
            all_data_yearly.to_csv(f,index=None)
            f.write("\n")
            logger.info(f"Created {opendata_filename}")
    else: 
        logger.info("There is no trash data")


    # Check numbers
    logger.info(f"There are {len(bi_campaigns_year)} campaigns recorded for year {year}.")
    campaigns_yearly = len(campaign_list)
    campaigns_with_data = len(all_data_yearly['campaign_id'].unique())
    campaigns_with_no_data = campaigns_yearly - campaigns_with_data
    logger.info(f"There are {campaigns_with_data} campaigns with data for {year} year.")
    logger.info(f"There are {campaigns_with_no_data} campaigns with no data for {year} year.")

    # Campaign with data and river is known
    known_river_df = all_data_yearly[all_data_yearly['river_name']!='unknown river']
    unique_known_river = known_river_df.drop_duplicates('campaign_id', keep='first')
    logger.info(f"There are {len(unique_known_river)} campaigns with data and known river for {year} year.")

    # Campaign with data and river is unknown
    unknown_river_df = all_data_yearly[all_data_yearly['river_name']=='unknown river']
    unique_unknown_river = unknown_river_df.drop_duplicates('campaign_id', keep='first')
    logger.info(f"There are {len(unique_unknown_river)} campaigns with data and unknown river for {year} year.")

    if country == 'france':
        # France Campaigns
        unique_france_campaigns = france_all_data_yearly.drop_duplicates('campaign_id', keep='first')
        logger.info(f"There are {len(unique_france_campaigns)} campaigns in France for {year} year.")

        # France Campaigns with data and river is known
        unique_france_with_known_river_all_data_yearly = france_with_known_river_all_data_yearly.drop_duplicates('campaign_id', keep='first')
        logger.info(f"There are {len(unique_france_with_known_river_all_data_yearly)} campaigns in France with known rivers for {year} year.")

        # France Campaigns with data and river is unknown
        unique_france_with_unknown_river_all_data_yearly = france_with_unknown_river_all_data_yearly.drop_duplicates('campaign_id', keep='first')
        logger.info(f"There are {len(unique_france_with_unknown_river_all_data_yearly)} campaigns in France with unknown rivers for {year} year.")

    # Open Data process summary
    if country == 'all':
       logger.info(f'There are {campaigns_with_data} campaigns written to {opendata_filename}')
    elif country == 'france':
        fr_river_campaigns_yearly = len(unique_france_with_known_river_all_data_yearly)
        logger.info(f'There are {fr_river_campaigns_yearly} campaigns written to {opendata_filename}')

    logger.info(f'Open Data creation executed successfuly.')


##### Main Execution ####
# Defining parser
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--country', choices=['france', 'all'], default='france',
                    help='specify whether you want opendata for France only or for all country')

parser.add_argument('-y', '--year', required=True,
                    help='specify the year you want opendata for')


# Create args parsing standard input
args = parser.parse_args()

# Run main
if __name__ == '__main__':
    main(args)