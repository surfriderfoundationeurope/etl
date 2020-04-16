from azure.storage.blob import ContainerClient
from azure.storage.blob import BlobClient

''' blobContainer create a name_list of blobs within container'''
''' params are container name (no full url) & storage conn string'''
def blobInContainer(connection_s,container_n):
    campaign_container = ContainerClient.from_connection_string(conn_str=connection_s, container_name=container_n)
    blob_list = campaign_container.list_blobs()
    blob_names_list = []
    for blob in blob_list:
        blob_names_list.append(blob.name)
    return blob_names_list

''' blobInfos provides basic information about a blob object'''
''' params are blob_name only (no full url) & storage conn string'''
def blobInfos(connection_s,container_n,blob_n):
    blob_video = BlobClient.from_connection_string(conn_str=connection_s,container_name=container_n, blob_name=blob_n)
    blob_video_url = blob_video.url
    blob_video_prop = blob_video.get_blob_properties()
    blob_video_prop_keys = blob_video_prop.keys()
    print("blob name:",blob_n)
    print("blob URL:",blob_video_url)
    print("blob properties:", blob_video_prop)
    print("blob properties keys:", blob_video_prop_keys)


''' downloadBlob from Azure to local file system'''
''' parameter is a blob client object from azure storage sdk'''
def downloadBlob(blobclient):
    with open("/tmp/"+blobclient.blob_name, "wb") as my_blob_dl:
        blob_data = blobclient.download_blob()
        blob_data.readinto(my_blob_dl)
    print("Blob %s downloaded" %blobclient.blob_name)
    print("Blob path: /tmp/%s" %blobclient.blob_name)
    path = "/tmp/"+blobclient.blob_name
    return path

print("hello from blob.py")