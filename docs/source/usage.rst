======
Usage
======

Launch CLI
----------

Once your environment `etl-env` is activate:
   .. code-block:: console

      >>> etl --help
           Usage: etl [OPTIONS]

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

In poduction
-------------
Coming soon, where to get the subscription info & co.