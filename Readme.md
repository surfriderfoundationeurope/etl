# Plastic Origin ETL
Welcome to Plastic Origin ETL project. It is part of a project led by [Surfrider Europe](https://surfrider.eu/), which aims at quantifying plastic pollution in rivers through space and time.

The ETL project implements an ETL (Extract Transform Load) process, to allow to produce Data that will be leveraged within Plastic Origin project. This Data will serve to build then analytics and reports of plastic pollution within rivers.

Next sections provides an overview of the ETL principles, as well as guidance to get started using the ETL.

Please note that this project is under active development and that frequent change and update happen over time.


## ETL Data Management Process
Overiew of ETL process architecture to insert Trash

![SFETLArch](https://user-images.githubusercontent.com/8882133/89392324-ae780480-d709-11ea-9dbb-c5518eb4ec91.png)


### ETL Scripts
The full ETL process rely on a Python script located [here](https://github.com/surfriderfoundationeurope/etl/blob/clem_dev/etl/etl.py). This script allows to locally run the full ETL process, that will download the media file to be processed (gopro, mobile, manual), extract and geolocalize Trashed and finally store the result as csv file or within PostGre Database server.

To process a gopro media without AI:
```bash
python etl.py -c campaign0 -b gopro.mp4 -p json -s gopro -t csv
```

To process a mobile media without AI:
```bash
python etl.py -c campaign0 -b mobile.mp4 -p json -s mobile -t csv
```

Script with Parameters:
This [script](https://github.com/surfriderfoundationeurope/etl/blob/clem_dev/etl/etl.py) takes the following argument parameter: 
```bash
python etl.py -h
usage: etl.py [-h] -c CONTAINERNAME -b BLOBNAME [-a AIURL] [-p {ai,json}]
              [-s {gopro,mobile,manual}] [-t {postgre,csv}]
```

The ETL script is the foundation to build the ETL API. The ETL API relies on the ETL scrit logic + Azure Function to easily creates a production REST API available in the Cloud.

### ETL Azure Function
After you installed [Azure function for Python pre-requesite](https://docs.microsoft.com/en-us/azure/azure-functions/functions-create-first-azure-function-azure-cli?pivots=programming-language-python&tabs=bash%2Cbrowser) on your local machine, you can run the ETL workflow as a local Azure function. 
Note you need to launch the function from within a python environment configured with ETL pre-requesite.
First go to /azfunction/etlAPIs/, then:

```bash
func start etlHttpTrigger/
```

This will run the ETL workflow as a local API using Azure function utilities.
You can therefore navigate to the ETL API endpoint using a browser, and execute the ETL process with.
Please note this will download the media file mobile.mp4 from Azure for which you need storage credential.
```bash
http://localhost:7071/api/etlHttpTrigger/?container=campaign0&blob=mobile.mp4&prediction=json&source=mobile&target=csv
```

When the AI inference service is running you would test it by calling the API with: 
```
http://localhost:7071/api/etlHttpTrigger/?container=campaign0&blob=mobile.mp4&prediction=ai&source=mobile&target=csv&aiurl=http://<AIURL>
```

When running the End to End process, download blob, making prediction with AI, writing to PostGre you would test with:
```
http://localhost:7071/api/etlHttpTrigger/?container=campaign0&blob=mobile.mp4&prediction=ai&source=mobile&target=postgre&aiurl=http://<AIURL>
```

### ETL Trigger Azure Function
The ETL Trigger Azure function defines additionnaly 3 x functions that will automatically call the ETL API when new media to process are stored in Azure.
They used the [blob trigger capabilities](https://docs.microsoft.com/fr-fr/azure/azure-functions/functions-bindings-storage-blob-trigger?tabs=python) defined within the [function.json] (https://github.com/surfriderfoundationeurope/etl/blob/clem_dev/azfunction/etlBlobTrigger/etlBlobTriggerGoPro/function.json).
Simplest way for testing is to publish directly to Azure with:
```
func azure functionapp publish <AZUREFUNCTIONApp>
```

### Docker
The GPS extraction subprocess requires to use binaries like ffmpeg which is not natively available within Python Azure Function. To address this requirement, the ETL Azure Function has been made available as a Docker image. 
The Docker file to build the image is located [here] (https://github.com/surfriderfoundationeurope/etl/blob/clem_dev/azfunction/etlAPIs/Dockerfile)
You will need to pass the appropriate credential at build time for the ETL to use Azure Storage and PostGre Database server.

### VM Scale Set
To overcome timeout limitation of native Azure Function service related to HTTP call and Load Balancer, the ETL APIs has also been made available to run on an Azure [Virtul Machine Scale Set](https://docs.microsoft.com/en-us/azure/virtual-machine-scale-sets/)
The related code for deployment is located [here](https://github.com/surfriderfoundationeurope/etl/tree/clem_dev/azfunction/etlAPIsVM)
To prepare the Virtual Machine for VM Scale Set deployment, the Azure related documentation can be found [here](https://docs.microsoft.com/en-us/azure/virtual-machine-scale-sets/tutorial-use-custom-image-cli)
