import functools
import logging
import os

from azure.core.exceptions import HttpResponseError
from azure.storage.blob import BlobClient
from azure.storage.blob import ContainerClient

from .exceptions import ETLError

logger = logging.getLogger()


def safe_blob(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            logger.warning(
                "Could not connect to blob storage. "
                "Connection string is either blank or malformed."
                "Early exit of ETL process !"
            )
            exit()

        except HttpResponseError as e:
            logger.warning(
                "Could not List blob, the container probably does not exist. "
                f"Details : {e} "
                "Early exit of ETL process !"
            )
            exit()

    return wrapper


@safe_blob
def list_container_blob_names(conn_str: str, container_name: str) -> list:
    """ List blob names in a given container

    Parameters
    ----------
    conn_str:  A connection string to an Azure Storage account.
    container_name:  The container name for the blob.

    Returns
    -------
    blob_names: list of blob names in the container
    """

    campaign_container = ContainerClient.from_connection_string(
        conn_str=conn_str, container_name=container_name
    )
    blob_names = [blob.name for blob in campaign_container.list_blobs()]
    return blob_names


@safe_blob
def download_blob(blob_client: BlobClient, local_path: str = "/tmp") -> str:
    """ Download Blob from Azure to local file system

    Parameters
    ----------
    blob_client: Azure client to interact with a specific blob
    local_path: Local path to download the blob in

    Returns
    -------
    download_dirctory: directory where blob content is downloaded
    """
    # todo: should we specify video name as well ?
    if not os.path.exists(local_path):
        os.mkdir(local_path)

    blob_name = blob_client.blob_name
    download_dirctory = os.path.join(local_path, blob_name)
    with open(download_dirctory, "wb") as blob_folder:
        blob_data = blob_client.download_blob()
        blob_data.readinto(blob_folder)
    logger.debug(
        f"Blob {blob_name} has been successfully downloaded. \n "
        f"Path to local storage : {download_dirctory}"
    )
    return download_dirctory
