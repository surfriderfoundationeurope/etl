# Plastic Origin Campaign0
Welcome to Plastic Origin Campaign0 project. It is part of a project led by [Surfrider Europe](https://surfrider.eu/), which aims at quantifying plastic pollution in rivers through space and time.

The Campaign0 project implements an ETL (Extract Transform Load) process, to allow to produce Data that will be leveraged within Plastic Origin project. This Data will serve to build then analytics and reports of plastic pollution within rivers.

Next sections provides an overview of the ETL principles, as well as guidance to get started using the ETL.

Please note that this project is under active development and that frequent change and update happen over time.


## ETL Data Management Process
Overiew of ETL process architecture to insert Trash

![SFETLArch](https://user-images.githubusercontent.com/8882133/79349912-1a561780-7f37-11ea-84fa-cd6e12ecf2c8.png)


### ETL Get started Notebook
To get started, easiest way it so execute the end2end_workflow notebooks [here](https://github.com/surfriderfoundationeurope/campaign0/blob/master/scripts/end2end_workflow.ipynb). This notebook allows to go trough the main steps of the ETL pipeline and understand the different building block: Azure Blob Operation, AI Operation, GPS operation, PostGre SQL operation.

Service Prequesite: ETL principle is a Data pipeline workflow between different source and destination. There are pre-requesite to connect to the different source and destination, typically connection string to access Blob Storage and PostGre SQL server. You also need the AI Inference service to be available, as it's a key component extracting Trashes from raw input Data.

Python Prerequesite: there are a bunch of python libraries required, for now on, please check this [script](https://github.com/surfriderfoundationeurope/campaign0/blob/master/scripts/etlworkflow.py) to have a look at import.


You can also find development notebooks in notebook folder, but be aware they are somehow deprecated. They remain available for further development and testing purpose.

### Scripts
There is work in-progress [here](https://github.com/surfriderfoundationeurope/campaign0/tree/master/scripts) to build the script architecture that will allow then deploy the ETL in production. Typically, we target to deploy the ETL process on top of Azure Function to support a serverless deployement architecture, or conversly to leverage open souce solution like Apache Airflow or Docker container to make the ETL portable, scalable and event-triggered.
