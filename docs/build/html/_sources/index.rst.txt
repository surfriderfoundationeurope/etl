.. Surfrider ETL documentation master file, created by
   sphinx-quickstart on Fri May  1 11:23:23 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Plastic Origin ETL's documentation!
==============================================

Plastic Origin is a project led by `Surfrider Europe
<https://surfrider.eu/>`_
aiming at identify and quantify plastic pollution in rivers through space and time.

This repository hosts the ETL (Extract Transform Load) pipeline,
consisting in downloading a media from a Blob storage, extracting
and transforming the GPX coordinates, computing AI trashes prediction
and insert it in database.
The data will then be used to build then analytics and reports of plastic pollution
within rivers.



.. toctree::
   :maxdepth: 6
   :caption: General Documentation

   general_documentation

.. toctree::
   :maxdepth: 2
   :caption: Getting started

   installation
   usage


.. toctree::
   :maxdepth: 10
   :caption: ETL script

   etl



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
