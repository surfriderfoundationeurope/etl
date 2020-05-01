============
Installation
============

Prerequisites
==============
- Python 3 distribution
- Clone the repository

   .. code-block:: console

      $ git clone https://github.com/surfriderfoundationeurope/etl

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