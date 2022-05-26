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
	curl  --request GET 'http://localhost:7071/api/etlHttpTrigger?container=manual&blob=50e1bd32-48c6-45e0-97d6-3cd4c688af8e.json&prediction=json&source=manual&target=csv&logid=a1bea0cd-580e-4ef5-850a-2025b464d516'

etl-api-test-mobile-csv:
	curl  --request GET 'http://localhost:7071/api/etlHttpTrigger?container=mobile&blob=6250052d-f716-435c-9d71-83ad49347c5e.mp4&prediction=json&source=mobile&target=csv&logid=778feb04-f1d2-471a-afe8-9d991d3a0a6a'

etl-api-test-gopro-csv:
	curl  --request GET 'http://localhost:7071/api/etlHttpTrigger?container=gopro&blob=b09a5594-988c-4fb3-9e95-11fd170f96b3.mp4&prediction=json&source=gopro&target=csv&logid=809ec466-1d71-49f6-b4a7-eea97966347f'

etl-api-test-manual-postgre:
	curl  --request GET 'http://localhost:7071/api/etlHttpTrigger?container=manual&blob=50e1bd32-48c6-45e0-97d6-3cd4c688af8e.json&prediction=json&source=manual&target=postgre&logid=a1bea0cd-580e-4ef5-850a-2025b464d516'

etl-api-test-mobile-postgre:
	curl  --request GET 'http://localhost:7071/api/etlHttpTrigger?container=mobile&blob=6250052d-f716-435c-9d71-83ad49347c5e.mp4&prediction=json&source=mobile&target=postgre&logid=778feb04-f1d2-471a-afe8-9d991d3a0a6a'

etl-api-test-mobile-postgre-2:
	curl  --request GET 'http://localhost:7071/api/etlHttpTrigger?container=mobile&blob=56c76b96-6248-4723-bf1e-8674a36f8877.mp4&prediction=json&source=mobile&target=postgre&logid=004622e2-b69c-49f8-9cd3-cf8ec567224b'

etl-api-test-gopro-postgre:
	curl  --request GET 'http://localhost:7071/api/etlHttpTrigger?container=gopro&blob=b09a5594-988c-4fb3-9e95-11fd170f96b3.mp4&prediction=json&source=gopro&target=postgre&logid=809ec466-1d71-49f6-b4a7-eea97966347f'


# ETL Docker
etl-build-docker: 
	docker build -t surfrider/etl:latest .

etl-run-docker: 
	docker run -p 8082:80 --restart always --name etl -e PGUSERNAME=${PGUSERNAME} -e PGDATABASE=${PGDATABASE} -e PGSERVER=${PGSERVER} -e PGPWD=${PGPWD} -e CONN_STRING=${CONN_STRING} surfrider/etl:latest


# ETL Docker local API & no AI (JSON Prediction)
etl-api-test-manual-csv:
	curl  --request GET 'http://localhost:8082/api/etlHttpTrigger?container=manual&blob=50e1bd32-48c6-45e0-97d6-3cd4c688af8e.json&prediction=json&source=manual&target=csv&logid=a1bea0cd-580e-4ef5-850a-2025b464d516'

etl-api-test-mobile-csv:
	curl  --request GET 'http://localhost:8082/api/etlHttpTrigger?container=mobile&blob=6250052d-f716-435c-9d71-83ad49347c5e.mp4&prediction=json&source=mobile&target=csv&logid=778feb04-f1d2-471a-afe8-9d991d3a0a6a'

etl-api-test-gopro-csv:
	curl  --request GET 'http://localhost:8082/api/etlHttpTrigger?container=gopro&blob=b09a5594-988c-4fb3-9e95-11fd170f96b3.mp4&prediction=json&source=gopro&target=csv&logid=809ec466-1d71-49f6-b4a7-eea97966347f'

etl-api-test-manual-postgre:
	curl  --request GET 'http://localhost:8082/api/etlHttpTrigger?container=manual&blob=50e1bd32-48c6-45e0-97d6-3cd4c688af8e.json&prediction=json&source=manual&target=postgre&logid=a1bea0cd-580e-4ef5-850a-2025b464d516'

etl-api-test-mobile-postgre:
	curl  --request GET 'http://localhost:8082/api/etlHttpTrigger?container=mobile&blob=6250052d-f716-435c-9d71-83ad49347c5e.mp4&prediction=json&source=mobile&target=postgre&logid=778feb04-f1d2-471a-afe8-9d991d3a0a6a'

etl-api-test-mobile-postgre-2:
	curl  --request GET 'http://localhost:8082/api/etlHttpTrigger?container=mobile&blob=56c76b96-6248-4723-bf1e-8674a36f8877.mp4&prediction=json&source=mobile&target=postgre&logid=004622e2-b69c-49f8-9cd3-cf8ec567224b'

etl-api-test-gopro-postgre:
	curl  --request GET 'http://localhost:8082/api/etlHttpTrigger?container=gopro&blob=b09a5594-988c-4fb3-9e95-11fd170f96b3.mp4&prediction=json&source=gopro&target=postgre&logid=809ec466-1d71-49f6-b4a7-eea97966347f'


