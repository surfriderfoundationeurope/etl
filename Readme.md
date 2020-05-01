# Plastic Origin ETL
Welcome to Plastic Origin ETL project. It is part of a project led by [Surfrider Europe](https://surfrider.eu/), which aims at quantifying plastic pollution in rivers through space and time.

The ETL project implements an ETL (Extract Transform Load) process, to allow to produce Data that will be leveraged within Plastic Origin project. This Data will serve to build then analytics and reports of plastic pollution within rivers.

Next sections provides an overview of the ETL principles, as well as guidance to get started using the ETL.

Please note that this project is under active development and that frequent change and update happen over time.


## ETL Data Management Process
Overiew of ETL process architecture to insert Trash

![SFETLArch](https://user-images.githubusercontent.com/8882133/79349912-1a561780-7f37-11ea-84fa-cd6e12ecf2c8.png)


### ETL Get started Notebook
To get started, easiest way it so execute the end2end_workflow notebooks [here](https://github.com/surfriderfoundationeurope/etl/blob/master/scripts/end2end_workflow.ipynb). This notebook allows to go trough the main steps of the ETL pipeline and understand the different building block: Azure Blob Operation, AI Operation, GPS operation, PostGre SQL operation.
Setup environment: You have the choice between virtual env or conda env: 
- conda env 
```terminal
cd scripts
conda env create -f  environment.yml 
conda activate etl-env
```
- virtual env
```terminal
cd scripts
python3 -m venv etl-env 
source etl-env-venv/bin/activate
pip install -r requirements 
```

Then, to launch `jupyter` : 
```terminal
jupyter notebook 
```

Service Prequesite: ETL principle is a Data pipeline workflow between different source and destination. There are pre-requesite to connect to the different source and destination, typically connection string to access Blob Storage and PostGre SQL server. You also need the AI Inference service to be available, as it's a key component extracting Trashes from raw input Data.

Python Prerequesite: there are a bunch of python libraries required, for now on, please check this [script](https://github.com/surfriderfoundationeurope/etl/blob/master/scripts/etlworkflow.py) to have a look at import.


You can also find development notebooks in notebook folder, but be aware they are somehow deprecated. They remain available for further development and testing purpose.

### Scripts
There is work in-progress [here](https://github.com/surfriderfoundationeurope/etl/tree/master/scripts) to build the script architecture that will allow then deploy the ETL in production. Typically, we target to deploy the ETL process on top of Azure Function to support a serverless deployement architecture, or conversly to leverage open souce solution like Apache Airflow or Docker container to make the ETL portable, scalable and event-triggered.

Get Started Script:
To get started executing the full ETL workflow, you can run the following [script](https://github.com/surfriderfoundationeurope/etl/blob/master/scripts/etlworkflow.py) with no argument:

```bash
python etlworkflow.py
```

This script will use a remote video file in blob storage, but requires you to have downloaded before the file 28022020_Boudigau_4.MP4 with full Data (2.5GB) including GPS in your local /tmp folder.

Script with Parameters:
This [script](https://github.com/surfriderfoundationeurope/etl/blob/master/scripts/etlworkflowargs.py) takes containername, blobname and videoname parameters. It's intended for production usage where the ETL would run again multiple videos within different containers in Azure Blob Storage.

```bash
python etlworkflowargs.py --containername <CONTAINERNAME> --blobname <BLOBNAME> --videoname <VIDEO.MP4> --aiurl <http://AIAPIURL>
```

Like for get started script, it's expected dowloading the file 28022020_Boudigau_4.MP4 locally to /tmp folder.
For production, this requirement will be removed. Only blob name will remain mandatory.

### Azure Function
After you installed [Azure function for Python pre-requesite](https://docs.microsoft.com/en-us/azure/azure-functions/functions-create-first-azure-function-azure-cli?pivots=programming-language-python&tabs=bash%2Cbrowser) on your local machine, you can run the ETL workflow as a local Azure function. 
First go to azfunction folder, then:

```bash
func start etlHttpTrigger/
```

This will run the ETL workflow as a local API using Azure function utilities.
You can therefore navigate to the ETL API endpoint using a browser, and execute the ETL process with:

```bash
http://localhost:7071/api/etlHttpTrigger?containername=<CONTAINERNAME>&blobname=<BLOBNAME>&videoname=<VIDEONAME>&aiurl=<http://AIURL>
```

Please note you still need the function to be running within a python environment with ETL pre-requesite, as well as the large local video file.
