# ETL Script
etl-script-manual-csv:
	python ../../etl/etl.py -c manual -b 50e1bd32-48c6-45e0-97d6-3cd4c688af8e.json -p json -s manual -t csv

etl-script-mobile-csv:
	python ../../etl/etl.py -c mobile -b 6250052d-f716-435c-9d71-83ad49347c5e.mp4 -p json -s mobile -t csv

etl-script-gopro-csv:
	python ../../etl/etl.py -c gopro -b b09a5594-988c-4fb3-9e95-11fd170f96b3.mp4 -p json -s gopro -t csv

etl-script-manual-postgre:
	python ../../etl/etl.py -c manual -b 50e1bd32-48c6-45e0-97d6-3cd4c688af8e.json -p json -s manual -t postgre

etl-script-mobile-postgre:
	python ../../etl/etl.py -c mobile -b 6250052d-f716-435c-9d71-83ad49347c5e.mp4 -p json -s mobile -t postgre

etl-script-gopro-postgre:
	python ../../etl/etl.py -c gopro -b b09a5594-988c-4fb3-9e95-11fd170f96b3.mp4 -p json -s gopro -t postgre


# ETL local API & no AI (JSON prediction)
etl-api-start:
	func start ../etlHttpTrigger

etl-api-test-manual-csv:
	curl  --request GET 'http://localhost:7071/api/etlHttpTrigger?container=manual&blob=50e1bd32-48c6-45e0-97d6-3cd4c688af8e.mp4&prediction=json&source=manual&target=csv'

etl-api-test-mobile-csv:
	curl  --request GET 'http://localhost:7071/api/etlHttpTrigger?container=mobile&blob=6250052d-f716-435c-9d71-83ad49347c5e.mp4&prediction=json&source=mobile&target=csv'

etl-api-test-gopro-csv:
	curl  --request GET 'http://localhost:7071/api/etlHttpTrigger?container=gopro&blob=b09a5594-988c-4fb3-9e95-11fd170f96b3.mp4&prediction=json&source=gopro&target=csv'

etl-api-test-manual-postgre:
	curl  --request GET 'http://localhost:7071/api/etlHttpTrigger?container=manual&blob=50e1bd32-48c6-45e0-97d6-3cd4c688af8e.mp4&prediction=json&source=manual&target=postgre'

etl-api-test-mobile-postgre:
	curl  --request GET 'http://localhost:7071/api/etlHttpTrigger?container=mobile&blob=6250052d-f716-435c-9d71-83ad49347c5e.mp4&prediction=json&source=mobile&target=postgre'

etl-api-test-gopro-postgre:
	curl  --request GET 'http://localhost:7071/api/etlHttpTrigger?container=gopro&blob=b09a5594-988c-4fb3-9e95-11fd170f96b3.mp4&prediction=json&source=gopro&target=postgre'


# ETL Docker
etl-build-docker: 
	docker build -t surfrider/etl:latest .

etl-run-docker: 
	docker run -p 8082:80 --restart always --name etl -e PGUSERNAME=${PGUSERNAME} -e PGDATABASE=${PGDATABASE} -e PGSERVER=${PGSERVER} -e PGPWD=${PGPWD} -e CONN_STRING=${CONN_STRING} surfrider/etl:latest


# ETL Docker local API & no AI (JSON Prediction)
etl-api-test-manual-csv:
	curl  --request GET 'http://localhost:8082/api/etlHttpTrigger?container=manual&blob=50e1bd32-48c6-45e0-97d6-3cd4c688af8e.mp4&prediction=json&source=manual&target=csv'

etl-api-test-mobile-csv:
	curl  --request GET 'http://localhost:8082/api/etlHttpTrigger?container=mobile&blob=6250052d-f716-435c-9d71-83ad49347c5e.mp4&prediction=json&source=mobile&target=csv'

etl-api-test-gopro-csv:
	curl  --request GET 'http://localhost:8082/api/etlHttpTrigger?container=gopro&blob=b09a5594-988c-4fb3-9e95-11fd170f96b3.mp4&prediction=json&source=gopro&target=csv'

etl-api-test-manual-postgre:
	curl  --request GET 'http://localhost:8082/api/etlHttpTrigger?container=manual&blob=50e1bd32-48c6-45e0-97d6-3cd4c688af8e.mp4&prediction=json&source=manual&target=postgre'

etl-api-test-mobile-postgre:
	curl  --request GET 'http://localhost:8082/api/etlHttpTrigger?container=mobile&blob=6250052d-f716-435c-9d71-83ad49347c5e.mp4&prediction=json&source=mobile&target=postgre'

etl-api-test-gopro-postgre:
	curl  --request GET 'http://localhost:8082/api/etlHttpTrigger?container=gopro&blob=b09a5594-988c-4fb3-9e95-11fd170f96b3.mp4&prediction=json&source=gopro&target=postgre'


