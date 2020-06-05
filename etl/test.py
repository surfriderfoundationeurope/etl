import os
import logging
from azure.storage.blob import ContainerClient
from azure.storage.blob import BlobClient
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


connection_string = os.getenv("CONN_STRING")
print(connection_string)

blob_list = list_blob_in_container(connection_string,'campaign0')
print(blob_list)