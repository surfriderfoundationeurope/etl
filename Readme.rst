Welcome to Plastic Origin ETL repository
=========================================

Plastic Origin is a project led by `Surfrider Europe
<https://surfrider.eu/>`_
aiming at identify and quantify plastic pollution in rivers through space and time.


Project Overview
================
Next sections provides an overview of the ETL principles, as well as guidance to get started using the ETL.

Please note that this project is under active development and that frequent change and update happen over time.


ETL Data Management Process
---------------------------
Overiew of ETL process architecture from blob download to database insertion.

.. image:: https://user-images.githubusercontent.com/8882133/79349912-1a561780-7f37-11ea-84fa-cd6e12ecf2c8.png
   :width: 600


Data sources
------------
Four main source of data:
  - GoPro 1080p 24 img/s: mp4 format containing video + GPS as GPX tracks
  - Smartphone 1080p 24 ou 30 img/s + GPS in a separate GPX file
  - Smartphone picture + GPS data
  - OSM Tracker data: GPX file containing way-points with labeled trash and their coordinates


Useful resources
----------------
Coming soon: Link to DB scheme, AI repository, ...



Installation
============

Prerequisites
-------------
- Python 3 distribution
- Clone the repository

   .. code-block:: console

      $ git clone https://github.com/surfriderfoundationeurope/etl
- Copy file `example.env`, rename in `.env` and
   set environment variables


Environment variables
---------------------

This environment variable is required if you work in data-mode 'azure' :

.. envvar:: CON_STRING

  To connect to Azure Blob Storage

This environment variable is required if you need to call the AI :

.. envvar:: AI_URL

  URL to AI API

These environment variables is required if you need to insert trash to db :

.. envvar:: PGSERVER, PGDATABASE, PGDATABASE, PGUSERNAME, PGPWD

  Info and identifier of PG database


Dev
---

1. Setup environment
---------------------

You have the choice between virtual env or conda env:

- conda env
   .. code-block:: console

      $ conda env create -f  environment.yml
      $ conda activate etl-env

- virtual env
   .. code-block:: console

      $ python3 -m venv etl-env
      $ source etl-env-venv/bin/activate
      $ pip install -r requirements


Usage
======

Launch CLI
----------

Once your environment `etl-env` is activate:
   .. code-block:: console

      >>> python etl_cli.py --help
           Usage: etl_cli.py [OPTIONS]

              Run the ETL

              Use command `python etl_cli.py --help` to get a list of the options .

            Options:
              --container TEXT                Name of Azure container to download the data
                                              from.

              --blob TEXT                     Name of Azure blob storage.
              --media TEXT                    Name of media to download the data from.
              --temp-dir DIRECTORY            Path to data directory to download the data.
              --data-dir DIRECTORY            Path to data directory to download the data.
                                              If given, data should be in local storage.
                                              (No download from Azure)

              --data-source [local|azure]     Source of data.
              --target-storage [local|postgre]
                                              Target to store the ETL output. If "local",
                                              will save in csv,  if "postgre", will insert
                                              each trash in Postgre database.

              --ai-url TEXT                   URL of AI. If not given, will be set from
                                              ENV.

              --help                          Show this message and exit.

Work 100% locally
------------------
- With local data as input
If you wish to work with local data instead of downloading data from Azure blob storage,
you need to set options `--data-source local --data-dir path/to/your/data/folder`

- Dump output in CSV file
If you wish to dump the ETL result locally, instead of connecting to Postgre database,
you need to set options  `--target-storage local` and you will get a file 'etl_output.csv'
in directory `temp-dir`, looking like:

.. csv-table:: etl_output.csv
   :file: etl_output.csv
   :header-rows: 4

- Example to test locally:
    - On GoPro data

    .. code-block:: console
        source etl-env-venv/bin/activate
        python etl_cli.py --data-source local --media sample.mp4  --data-dir  data/gopro/ --target-storage local

    - On OSM Tracker file

    .. code-block:: console
        source etl-env-venv/bin/activate
        python etl_cli.py --data-source local --media sample.gpx  --data-dir  data/osm_tracker/ --target-storage local

    - On Smartphone video

    .. code-block:: console
        source etl-env-venv/bin/activate
        python etl_cli.py --data-source local --media sample.mp4  --data-dir  data/osm_tracker/ --target-storage local



In poduction
-------------
Coming soon, where to get the subscription info & co.

Work In Progress
================
Notebooks
---------
There is work in-progress [here](https://github.com/surfriderfoundationeurope/etl/tree/master/scripts) to build the script architecture that will allow then deploy the ETL in production. Typically, we target to deploy the ETL process on top of Azure Function to support a serverless deployement architecture, or conversly to leverage open souce solution like Apache Airflow or Docker container to make the ETL portable, scalable and event-triggered.


Azure function
--------------
After you installed [Azure function for Python pre-requesite](https://docs.microsoft.com/en-us/azure/azure-functions/functions-create-first-azure-function-azure-cli?pivots=programming-language-python&tabs=bash%2Cbrowser) on your local machine, you can run the ETL workflow as a local Azure function. 
First go to azfunction folder, then:

 .. code-block:: console
      func start etlHttpTrigger/

This will run the ETL workflow as a local API using Azure function utilities.
You can therefore navigate to the ETL API endpoint using a browser, and execute the ETL process with:

 .. code-block:: console
    http://localhost:7071/api/etlHttpTrigger?containername=<CONTAINERNAME>&blobname=<BLOBNAME>&videoname=<VIDEONAME>&aiurl=<http://AIURL>

Please note you still need the function to be running within a python environment with ETL pre-requesite, as well as the large local video file.
