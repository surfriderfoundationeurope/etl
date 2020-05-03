################################################################################
# Preliminary stage where Surfrider private projects will be installed
# This is a preliminary image in order to avoid saving sensitive information on
# the final docker image. For example, the git credentials.
FROM python:3.7-slim as intermediate

# Additional packages not included in the base image
RUN apt-get update && apt-get install -y --no-install-recommends \
    git openssh-client build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /root/.ssh/
# You need to generate these secret files, check the README
ADD conf/github /root/.ssh/id_rsa
ADD conf/github.pub /root/.ssh/id_rsa.pub
# make sure bitbucket domain is accepted
RUN touch /root/.ssh/known_hosts
RUN ssh-keyscan github.com >> /root/.ssh/known_hosts

# install all OMI requirements as wheels
RUN mkdir /tmp/wheels
WORKDIR /tmp
ADD requirements.txt .
RUN pip install --upgrade pip==20.0.2 && \
    pip wheel --wheel-dir /tmp/wheels -r requirements.txt

################################################################################
# To enable ssh & remote debugging on app service change the base image to the one below
FROM mcr.microsoft.com/azure-functions/python:3.0-python3.7-appservice
#FROM mcr.microsoft.com/azure-functions/python:3.0-python3.7

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

RUN apt-get install -y git ffmpeg vim

# Install dependencies from wheels generated in intermediate image
COPY --from=intermediate /tmp/wheels /tmp/wheels
#Explanation: to build Psycopg you need the packages gcc musl-dev postgresql-dev.
#Then you also need that pg_config executable: while simply installing postgresql-dev
#will work, postgresql-libs does fine too and takes up some 12 MB less space.
# Stack-Overflow: https://stackoverflow.com/questions/46711990/error-pg-config-executable-not-found-when-installing-psycopg2-on-alpine-in-dock
#RUN \
# apk add --no-cache postgresql-libs && \
# apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
# /usr/local/bin/python -m pip install --upgrade pip
# python3 -m pip install -r requirements.txt --no-cache-dir && \
# pip install /tmp/wheels/*.whl && \
# apk --purge del .build-deps

RUN pip install /tmp/wheels/*.whl
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install /tmp/wheels/*.whl

# Copy and install etl
RUN mkdir /code
WORKDIR /code
COPY setup.cfg setup.py  ./
COPY etl ./etl
RUN pip install .
