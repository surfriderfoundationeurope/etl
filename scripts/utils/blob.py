from azure.storage.blob import ContainerClient
from azure.storage.blob import BlobClient
import logging

logger = logging.getLogger()

def list_blob_in_container(connection_s:str,container_n:str)->list:
    """ list the blobs within a given container of an Azure storage account
    Helper function for debugging in case no access to azure

    Arguments:
        connection_s {str} -- an azure storage account connection string
        container_n {str} -- a container within a storage account

    Returns:
        blob_names_list -- the list of blobs within container
    """
    try:
        campaign_container = ContainerClient.from_connection_string(conn_str=connection_s, container_name=container_n)
        blob_list = campaign_container.list_blobs()
        blob_names_list = []
        for blob in blob_list:
            blob_names_list.append(blob.name)
        return blob_names_list
    except:
        logger.info("The container you are trying to list blob from probably does not exist.")
        logger.info("Early exit of ETL process as container probably does not exist.")
        exit()


def get_blob_infos(connection_s:str,container_n:str,blob_n:str):
    ''' 
    blobInfos provides basic information about a blob object
    Input: params are storage conn string, container name and blob_name only (no full url)
    Output: None, print only
    '''
    try:
        blob_video = BlobClient.from_connection_string(conn_str=connection_s,container_name=container_n, blob_name=blob_n)
        blob_video_url = blob_video.url
        print("Blob URL:",blob_video_url)
    except: 
        print("The blob you are trying to get info from probably does not exist.")


def download_blob(blobclient:object)->str:
    ''' 
    downloadBlob from Azure to local file system
    Input: parameter is a blob client object from azure storage sdk
    Output: output is the path of the downloaded blob
    '''

    try:
        with open("/tmp/"+blobclient.blob_name, "wb") as my_blob_dl:
            blob_data = blobclient.download_blob()
            blob_data.readinto(my_blob_dl)
        logger.info(f'Blob {blobclient.blob_name} downloaded within /tmp/{blobclient.blob_name}' )
        path = "/tmp/"+blobclient.blob_name
        return path
    except:
        logger.error("The blob you are trying to download probably does not exist within container.")
        logger.error("Early exit of ETL process.")
        exit()