import logging
import requests

import azure.functions as func

logging.basicConfig(level=logging.INFO)


def main(etlblob: func.InputStream):
    logging.info(f"Python blob trigger function processed blob \n"
                 f"Name: {etlblob.name}\n"
                 f"Blob Size: {etlblob.length} bytes")

    url = f'http://etlapiplastico-dev.westeurope.cloudapp.azure.com:8082/api/etlHttpTrigger?container=campaign0&blob={etlblob.name}&prediction=json&source=gopro&target=csv'
    payload = {}
    headers= {}
    response = requests.request("GET", url, headers=headers, data = payload)
    logging.info(response.text.encode('utf8'))
    