# To enable ssh & remote debugging on app service change the base image to the one below
FROM mcr.microsoft.com/azure-functions/python:3.0-python3.7-appservice
#FROM mcr.microsoft.com/azure-functions/python:3.0-python3.7

# install all OMI requirements as wheels
RUN mkdir /tmp/wheels
WORKDIR /tmp
ADD requirements.txt .
RUN pip install --upgrade pip==20.0.2 && \
    pip wheel --wheel-dir /tmp/wheels -r requirements.txt


RUN pip install /tmp/wheels/*.whl
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install /tmp/wheels/*.whl

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

RUN apt-get update && apt-get install -y git ffmpeg vim

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY . /home/site/wwwroot

