============
Installation
============

Prerequisites
==============
- Python 3 distribution
- Clone the repository

   .. code-block:: console

      $ git clone https://github.com/surfriderfoundationeurope/etl
- Copy file `example.env`, rename in `.env` and
   set environment variables


Environment variables
=====================

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
===

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

2. Launch CLI
--------------
Once your environment is activate:
   .. code-block:: console

      $ python etl_cli.py --help

Prod: Azure deployment
======================
Coming soon: How to deploy ?
