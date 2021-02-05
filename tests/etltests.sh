# ETL Script
# gopro
python etl.py -c gopro -b 56c76b96-6248-4723-bf1e-8674a36f8877.mp4  -p json -t csv -s gopro
python etl.py -c gopro -b 56c76b96-6248-4723-bf1e-8674a36f8877.mp4 -p json -t postgre -s gopro
python etl.py -c gopro -b 56c76b96-6248-4723-bf1e-8674a36f8877.mp4 -a <aiurl> -p ai -t csv -s gopro
python etl.py -c gopro -b 56c76b96-6248-4723-bf1e-8674a36f8877.mp4 -a <aiurl> -p ai -t postgre -s gopro

# mobile
python etl.py -c mobile -b 6250052d-f716-435c-9d71-83ad49347c5e.mp4 -p json -t csv -s mobile
python etl.py -c mobile -b 6250052d-f716-435c-9d71-83ad49347c5e.mp4 -p json -t postgre -s mobile
python etl.py -c mobile -b 6250052d-f716-435c-9d71-83ad49347c5e.mp4 -a <aiurl> -p ai -t csv -s mobile
python etl.py -c mobile -b 6250052d-f716-435c-9d71-83ad49347c5e.mp4 -a <aiurl> -p ai -t postgre -s mobile

# manual
python etl.py -c manual -b 6250052d-f716-435c-9d71-83ad49347c5e.json -p json -t csv -s manual
python etl.py -c manual -b 6250052d-f716-435c-9d71-83ad49347c5e.json -p json -t postgre -s manual


# ETL API
# gopro
curl --location --request GET '<etlurl>/api/etlHttpTrigger/?container=gopro&blob=56c76b96-6248-4723-bf1e-8674a36f8877.mp4&prediction=json&source=gopro&target=csv'
curl --location --request GET '<etlurl>/api/etlHttpTrigger/?container=gopro&blob=56c76b96-6248-4723-bf1e-8674a36f8877.mp4&prediction=json&source=gopro&target=postgre'
curl --location --request GET '<etlurl>/api/etlHttpTrigger/?container=gopro&blob=56c76b96-6248-4723-bf1e-8674a36f8877.mp4&prediction=ai&source=gopro&target=csv&aiurl=<aiurl>'
curl --location --request GET '<etlurl>/api/etlHttpTrigger/?container=gopro&blob=56c76b96-6248-4723-bf1e-8674a36f8877.mp4&prediction=ai&source=gopro&target=postgre&aiurl=<aiurl>'

# mobile
curl --location --request GET '<etlurl>/api/etlHttpTrigger/?container=mobile&blob=6250052d-f716-435c-9d71-83ad49347c5e.mp4&prediction=json&source=mobile&target=csv'
curl --location --request GET '<etlurl>/api/etlHttpTrigger/?container=mobile&blob=6250052d-f716-435c-9d71-83ad49347c5e.mp4&prediction=json&source=mobile&target=postgre'
curl --location --request GET '<etlurl>/api/etlHttpTrigger/?container=mobile&blob=6250052d-f716-435c-9d71-83ad49347c5e.mp4&prediction=ai&source=mobile&target=csv&aiurl=<aiurl>'
curl --location --request GET '<etlurl>/api/etlHttpTrigger/?container=mobile&blob=6250052d-f716-435c-9d71-83ad49347c5e.mp4&prediction=ai&source=mobile&target=postgre&aiurl=<aiurl>'

# manual
curl --location --request GET '<etlurl>/api/etlHttpTrigger?container=manual&blob=6250052d-f716-435c-9d71-83ad49347c5e.json&prediction=json&source=manual&target=csv'
curl --location --request GET '<etlurl>/api/etlHttpTrigger?container=manual&blob=6250052d-f716-435c-9d71-83ad49347c5e.json&prediction=json&source=manual&target=postgre'