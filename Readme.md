<h1 align="left">Plastic Origin ETL</h1>

<a href="https://www.plasticorigins.eu/"><img width="80px" src="https://github.com/surfriderfoundationeurope/The-Plastic-Origins-Project/blob/master/assets/PlasticOrigins_logo.png" width="5%" height="5%" align="left" hspace="0" vspace="0"></a>

  <p align="justify">Proudly Powered by <a href="https://surfrider.eu/">SURFRIDER Foundation Europe</a>, this open-source initiative is a part of the <a href="https://www.plasticorigins.eu/">PLASTIC ORIGINS</a> project - a citizen science project that uses AI to map plastic pollution in European rivers and share its data publicly. Browse the <a href="https://github.com/surfriderfoundationeurope/The-Plastic-Origins-Project">project repository</a> to know more about its initiatives and how you can get involved. Please consider starring :star: the project's repositories to show your interest and support. We rely on YOU for making this project a success and thank you in advance for your contributions.</p>

_________________

<!--- OPTIONAL: You can add badges and shields to reflect the current status of the project, the licence it uses and if any dependencies it uses are up-to-date. Plus they look pretty cool! You can find a list of badges or design your own at https://shields.io/ --->

Welcome to **Plastic Origin ETL**, an ETL (Extract Transform Load) Data Management process allowing to produce Data that will be leveraged within the Plastic Origin project. This Data will serve to build then analytics and reports of plastic pollution within rivers.

>Please note this project is under development and that frequent changes and updates happen over time.

## **Getting Started**

### **Prerequisites**

Before you begin, ensure you have met the following requirements:

* You have a `<Windows/Linux/Mac>` machine supporting python.
* You have installed requirements.txt with pip install -r requirements.txt
* You have installed locally the latest version of [azure function](https://docs.microsoft.com/fr-fr/azure/azure-functions/create-first-function-cli-python?tabs=azure-cli%2Cbash%2Cbrowser#configure-your-local-environment) for python.

#### **Technical stack**

* Language: `Python`
* Framework: `Python 3.7`
* Unit test framework: `NA`

## **Installation**
### **ETL local API**
The ETL API can be locally deployed using the [Azure function framework](https://learn.microsoft.com/en-us/azure/azure-functions/create-first-function-cli-python?tabs=azure-cli%2Cbash&pivots=python-mode-configuration).
#### **Pre-requesite**: 
It's recommended that you use python virtual environement before installing packages with pip. You also have to set the following environment variables:
CONN_STRING, PGSERVER, PGDATABASE, PGUSERNAME, PGPWD. 
#### **Deploy local ETL API**:
```bash
cd src/batch/etlAPI/

pip install -r requirements

func start etlHttpTrigger
```

#### **Build Docker ETL API**
The GPS extraction subprocess requires to use binaries like ffmpeg which is not natively available within Python Azure Function. To address this requirement, the ETL Azure Function has been made available as a Docker image. 
The Docker file to build the image is located [here](https://github.com/surfriderfoundationeurope/etl/blob/clem_dev/azfunction/etlAPIs/Dockerfile)
You will need to pass the appropriate credential at run time for the ETL to use correctly Azure Storage and PostGre Database server.

```bash
cd src/batch/etlAPI/

docker build -t surfrider/etl:latest .
```

#### **Run Docker ETL API**
```bash
cd src/batch/etlAPI/

docker run -p 8082:80 --restart always --name etl -e PGUSERNAME=${PGUSERNAME} -e PGDATABASE=${PGDATABASE} -e PGSERVER=${PGSERVER} -e PGPWD=${PGPWD} -e CONN_STRING=${CONN_STRING} surfrider/etl:latest
```

## **Usage**

### **Call local ETL API**:
#### **Option**: 
**target**: csv or postgre, **prediction**: json or ai
#### **Port**: 
**7071** for local API, **8082** for docker API
##### No Surfnet AI
```bash
manual: curl --request GET 'http://localhost:<port>/api/etlHttpTrigger?container=manual&blob=<blobname>&prediction=json&source=manual&target=csv&logid=<logid>'
mobile: curl --request GET 'http://localhost:<port>/api/etlHttpTrigger?container=mobile&blob=<blobname>&prediction=json&source=mobile&target=csv&logid=<logid>'
gopro:  curl --request GET 'http://localhost:<port>/api/etlHttpTrigger?container=gopro&blob=<blobname>&prediction=json&source=gopro&target=csv&logid=<logid>'
```

##### With Surfnet AI
```bash
mobile: curl --request GET 'http://localhost:<port>/api/etlHttpTrigger?container=mobile&blob=<blobname>&prediction=ai&source=mobile&target=csv&aiurl=<aiurl>&logid=<logid>'
gopro:  curl  --request GET 'http://localhost:<port>/api/etlHttpTrigger?container=gopro&blob=<blobname>&prediction=ai&source=gopro&target=csv&aiurl=<aiurl>&logid=<logid>'
```

#### **ETL Trigger Azure Function**
The ETL Trigger Azure function defines additionnaly 3 x functions that will automatically call the ETL API when new media to process are stored in Azure.
They used the [blob trigger capabilities](https://docs.microsoft.com/fr-fr/azure/azure-functions/functions-bindings-storage-blob-trigger?tabs=python) defined within the [function.json](https://github.com/surfriderfoundationeurope/etl/blob/clem_dev/azfunction/etlBlobTrigger/etlBlobTriggerGoPro/function.json).
Simplest way for testing is to publish directly to Azure with:
```bash
cd src/batch/etlBlobTrigger/

func azure functionapp publish <AZUREFUNCTIONApp>
```


## **ETL Deployment Architecture**
The ETL is made of three parts: 
* The BlobTrigger function which is triggered by new media
* The ETL API function which does the actual ETL process
* The ETL batch which is a DAG running on Airflow

## Recipe for re-running ETL on data


  

If you want to re-run the full processing from starting data:
- We assume that files (.json and .mp4 if automatic) are present in the blob storage
- We assume that the blob trigger worked properly and the table `campaign.campaign` contains the campaign details.

There are two steps
<details> 
  <summary>trigger_batch_etl_all</summary>

  The `trigger_batch_etl_all` will re-insert the trash in `campaign.trash`. To rerun this process for a given campaign `campaign_id`, you need to:
  - remove the rows in `campaing.trash` which corresponds to the `campaign_id`
  - In `logs.etl` row with the corresponding `campaign_id`, set the column "status" to "notprocessed"
  
  You may then run the `trigger_batch_etl_all` DAG.
</details>

  
<details> 
  <summary>bi processing and postprocessing</summary>

  The `bi-processing` will recompute the different metrics related to the trash and campaign. To rerun this process for a given campaign `campaign_id`, you need to:
  - In table `campaign.campaign` row `campaign_id`, set the column "has_been_computed" to NULL
  - Remove the line corresponing to `campaign_id` in `bi_temp.pipelines`
  
  You may then run the `bi-processing` DAG which will update the `bi` tables and run `bi-postprocessin`
</details>


## **Contributing**

It's great to have you here! We welcome any help and thank you in advance for your contributions.

* Feel free to **report a problem/bug** or **propose an improvement** by creating a [new issue](https://github.com/surfriderfoundationeurope/labelcv-web/issues). Please document as much as possible the steps to reproduce your problem (even better with screenshots). If you think you discovered a security vulnerability, please contact directly our [Maintainers](##Maintainers).

* Take a look at the [open issues](https://github.com/surfriderfoundationeurope/labelcv-web/issues) labeled as `help wanted`, feel free to **comment** to share your ideas or **submit a** [**pull request**](https://github.com/surfriderfoundationeurope/labelcv-web/pulls) if you feel that you can fix the issue yourself. Please document any relevant changes.

## **Maintainers**

If you experience any problems, please don't hesitate to ping:

* [@cl3m3nt](https://github.com/cl3m3nt)
* [@charlesollion](https://github.com/charlesollion)

Special thanks to all our [Contributors](https://github.com/orgs/surfriderfoundationeurope/people).

## **License**

We’re using the `MIT` License. For more details, check [`LICENSE`](https://github.com/surfriderfoundationeurope/etl/blob/master/LICENSE) file.

