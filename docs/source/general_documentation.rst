=================
Project Overview
=================

Next sections provides an overview of the ETL principles, as well as guidance to get started using the ETL.

Please note that this project is under active development and that frequent change and update happen over time.



ETL Data Management Process
===========================
Overiew of ETL process architecture from blob download to database insertion.

.. image:: https://user-images.githubusercontent.com/8882133/79349912-1a561780-7f37-11ea-84fa-cd6e12ecf2c8.png
   :width: 600


Data sources
============
Four main source of data:
  - GoPro 1080p 24 img/s: mp4 format containing video + GPS as GPX tracks
  - Smartphone 1080p 24 ou 30 img/s + GPS in a separate GPX file
  - Smartphone picture + GPS data
  - OSM Tracker data: GPX file containing way-points with labeled trash and their coordinates
See samples of those in folder /data.

Useful resources
================
Coming soon: Link to DB scheme, AI repository, ...