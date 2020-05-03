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


Guidelines
==========

Install this package by adding the following line to your
``environment.yaml`` file as follows:

.. code-block:: yaml

    name: ...
    dependencies:
    - pip
    - pip:
        - git+ssh://git@github.com/surfriderfoundationeurope/etl.git@vX.Y.Z#egg=etl
        # or
        - git+https://github.com/surfriderfoundationeurope/etl.git@vX.Y.Z#egg=etl

where ``vX.Y.Z`` is the exact version number that you need.

If you want to develop on Surfrider ETL *at the same time* that you are
developing some other project, clone this repository and install it on
development mode:

.. code-block:: console

    $ git clone git+ssh://git@github.com/surfriderfoundationeurope/etl.git
    $ cd etl
    $ pip install -e .

Note that this *development mode* is not recommended for reproducible analyses
because you might end up with a locally modified version that is not available
to other people.

How to create virtual/conda env ?
---------------------------------
You have the choice between virtual env or conda env:

- conda env
   .. code-block:: console

      $ conda env create -f  environment.yml
      $ conda activate etl-env

- virtual env
   .. code-block:: console

      $ python3 -m venv etl-env
      $ source etl-env/bin/activate
      $ pip install -r requirements.txt

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


Prod: Docker / Azure deployment
===============================
   .. code-block:: console

      $ docker build .

Coming soon: How to deploy ?
