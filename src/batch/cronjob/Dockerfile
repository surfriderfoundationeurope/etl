FROM python:3.8-buster

ADD requirements.txt .

RUN pip install -r requirements.txt

ADD ./cron_trigger_batch_etl_all.py .
ADD ./postgre.py .
ADD ./exceptions.py .

ENTRYPOINT ["python", "cron_trigger_batch_etl_all.py"]