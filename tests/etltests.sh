## ETL OLD ##
# gopro
python etl_old.py -c campaign0 -b 28022020_Boudigau_4_short_480.mov -v 28022020_Boudigau_4.MP4 -p json -t csv -s gopro
python etl_old.py -c campaign0 -b 28022020_Boudigau_4_short_480.mov -v 28022020_Boudigau_4.MP4 -p json -t postgre -s gopro
python etl_old.py -c campaign0 -b 28022020_Boudigau_4_short_480.mov -v 28022020_Boudigau_4.MP4 -a http://aiapiplastico-dev.westeurope.cloudapp.azure.com -p ai -t csv -s gopro
python etl_old.py -c campaign0 -b 28022020_Boudigau_4_short_480.mov -v 28022020_Boudigau_4.MP4 -a http://aiapiplastico-dev.westeurope.cloudapp.azure.com -p ai -t postgre -s gopro

# mobile
python etl_old.py -c campaign0 -b 28022020_Boudigau_2.mp4 -v 28022020_Boudigau_2.mp4 -p json -t csv -s mobile
python etl_old.py -c campaign0 -b 28022020_Boudigau_2.mp4 -v 28022020_Boudigau_2.mp4 -p json -t postgre -s mobile
python etl_old.py -c campaign0 -b 28022020_Boudigau_2.mp4 -v 28022020_Boudigau_2.mp4 -a http://aiapiplastico-dev.westeurope.cloudapp.azure.com -p ai -t csv -s mobile
python etl_old.py -c campaign0 -b 28022020_Boudigau_2.mp4 -v 28022020_Boudigau_2.mp4 -a http://aiapiplastico-dev.westeurope.cloudapp.azure.com -p ai -t postgre -s mobile

# manual
python etl_old.py -c campaign0 -b ADOUR.1_AVRIL_2019.ANTOINE_G1.gpx -v 28022020_Boudigau_4.MP4 -a http://aiapiplastico-dev.westeurope.cloudapp.azure.com -p json -t csv -s manual
python etl_old.py -c campaign0 -b ADOUR.1_AVRIL_2019.ANTOINE_G1.gpx -v 28022020_Boudigau_4.MP4 -a http://aiapiplastico-dev.westeurope.cloudapp.azure.com -p json -t postgre -s manual


## ETL ##

## AZURE Data ##
# gopro
python etl.py -c campaign0 -b 28022020_Boudigau_4.MP4 -p json -t csv -s gopro
python etl.py -c campaign0 -b 28022020_Boudigau_4.MP4 -p json -t postgre -s gopro
python etl.py -c campaign0 -b 28022020_Boudigau_4.MP4 -a http://aiapiplastico-dev.westeurope.cloudapp.azure.com -p ai -t csv -s gopro
python etl.py -c campaign0 -b 28022020_Boudigau_4.MP4 -a http://aiapiplastico-dev.westeurope.cloudapp.azure.com -p ai -t postgre -s gopro

# mobile
python etl.py -c campaign0 -b 28022020_Boudigau_2.mp4 -p json -t csv -s mobile
python etl.py -c campaign0 -b 28022020_Boudigau_2.mp4 -p json -t postgre -s mobile
python etl.py -c campaign0 -b 28022020_Boudigau_2.mp4 -a http://aiapiplastico-dev.westeurope.cloudapp.azure.com -p ai -t csv -s mobile
python etl.py -c campaign0 -b 28022020_Boudigau_2.mp4 -a http://aiapiplastico-dev.westeurope.cloudapp.azure.com -p ai -t postgre -s mobile

# manual
python etl.py -c campaign0 -b ADOUR.1_AVRIL_2019.ANTOINE_G1.gpx -p json -t csv -s manual
python etl.py -c campaign0 -b ADOUR.1_AVRIL_2019.ANTOINE_G1.gpx -p json -t postgre -s manual


## LOCAL Data ##
# gopro
python etl.py -c campaign0 -b gopro.mp4 -p json -t csv -s gopro
python etl.py -c campaign0 -b gopro.mp4 -p json -t postgre -s gopro
python etl.py -c campaign0 -b gopro.mp4 -a http://aiapiplastico-dev.westeurope.cloudapp.azure.com -p ai -t csv -s gopro
python etl.py -c campaign0 -b gopro.mp4 -a http://aiapiplastico-dev.westeurope.cloudapp.azure.com -p ai -t postgre -s gopro

# mobile
python etl.py -c campaign0 -b mobile.mp4 -p json -t csv -s mobile
python etl.py -c campaign0 -b mobile.mp4 -p json -t postgre -s mobile
python etl.py -c campaign0 -b mobile.mp4 -a http://aiapiplastico-dev.westeurope.cloudapp.azure.com -p ai -t csv -s mobile
python etl.py -c campaign0 -b mobile.mp4 -a http://aiapiplastico-dev.westeurope.cloudapp.azure.com -p ai -t postgre -s mobile

# manual
python etl.py -c campaign0 -b manual.gpx -p json -t csv -s manual
python etl.py -c campaign0 -b manual.gpx -p json -t postgre -s manual