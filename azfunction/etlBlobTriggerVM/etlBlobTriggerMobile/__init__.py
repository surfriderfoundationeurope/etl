import logging
import requests

import azure.functions as func

logging.basicConfig(level=logging.INFO)


def main(etlblob: func.InputStream):
    logging.info(f"Python blob trigger function processed blob \n"
                 f"Name: {etlblob.name}\n"
                 f"Blob Size: {etlblob.length} bytes")
    blob_fullname = etlblob.name
    container = blob_fullname.split('/')[0]
    blob_name = blob_fullname.split('/')[1]
    source = 'mobile'
    aiurl = 'http://aiapivmssplastico-prod.northeurope.cloudapp.azure.com'
    url = f'http://etlapivmssplastico-prod.northeurope.cloudapp.azure.com:8081/api/etlHttpTrigger?container={container}&blob={blob_name}&prediction=ai&aiurl={aiurl}&source={source}&target=postgre'
    payload = {}
    headers= {}
    response = requests.request("GET", url, headers=headers, data = payload)
    logging.info(response.text.encode('utf8'))
    logging.info(f'Sent Request to ETL to process blob {blob_name} from Mobile source')
    