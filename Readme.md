<h1 align="left">Plastic Origin ETL</h1>

<a href="https://www.plasticorigins.eu/"><img width="80px" src="https://github.com/surfriderfoundationeurope/The-Plastic-Origins-Project/blob/master/assets/PlasticOrigins_logo.png" width="5%" height="5%" align="left" hspace="0" vspace="0"></a>

  <p align="justify">Proudly Powered by <a href="https://surfrider.eu/">SURFRIDER Foundation Europe</a>, this open-source initiative is a part of the <a href="https://www.plasticorigins.eu/">PLASTIC ORIGINS</a> project - a citizen science project that uses AI to map plastic pollution in European rivers and share its data publicly. Browse the <a href="https://github.com/surfriderfoundationeurope/The-Plastic-Origins-Project">project repository</a> to know more about its initiatives and how you can get involved. Please consider starring :star: the project's repositories to show your interest and support. We rely on YOU for making this project a success and thank you in advance for your contributions.</p>

_________________

<!--- OPTIONAL: You can add badges and shields to reflect the current status of the project, the licence it uses and if any dependencies it uses are up-to-date. Plus they look pretty cool! You can find a list of badges or design your own at https://shields.io/ --->

<!--- TODO: Give a short introduction of product. Let this section explain the objectives or the motivation behind this product. Add a line of information text about what the product does. Your introduction should be around 2 or 3 sentences.--->

<!--- These are just example (copied from current readme file): add, duplicate or remove as required --->

Welcome to **Plastic Origin ETL**, an ETL (Extract Transform Load) Data Management process allowing to produce Data that will be leveraged within the Plastic Origin project. This Data will serve to build then analytics and reports of plastic pollution within rivers.

**Overiew of ETL Data Management process architecture to insert Trash:**

![SFETLArch](https://user-images.githubusercontent.com/8882133/89392324-ae780480-d709-11ea-9dbb-c5518eb4ec91.png)

>Please note that this project is under active development and that frequent changes and updates happen over time.

## **Getting Started**
<!--- TODO: Guide users through getting your code up and running on their own system.--->

### **Prerequisites**

Before you begin, ensure you have met the following requirements:
<!--- These are just example requirements. Add, duplicate or remove as required --->
* You have a `<Windows/Linux/Mac>` machine supporting python.
<!--- One more example from other project's repo: --->
* You have installed requirements.txt with pip install -r requirements.txt
* You have installed locally the latest version of [azure function](https://docs.microsoft.com/fr-fr/azure/azure-functions/create-first-function-cli-python?tabs=azure-cli%2Cbash%2Cbrowser#configure-your-local-environment) for python.

#### **Technical stack**
<!--- These are just example from other project's repo: add, duplicate or remove as required --->
* Language: `Python`
* Framework: `Python 3.7`
* Unit test framework: `NA`

### **Installation**

<!--- TODO: It's a code block illustrating how to install. Include any system-specific information needed for installation. If there are multiple versions which the user may interface with, an updating section would be useful. Add Dependencies subsection if there are unusual dependencies or dependencies that must be manually installed.--->

<!--- These are just example (copied from current readme file): add, duplicate or remove as required --->
**ETL script**

The full ETL process relies on a Python script located [here](https://github.com/surfriderfoundationeurope/etl/blob/clem_dev/etl/etl.py). This script allows to locally run the full ETL process, that will download the media file to be processed (gopro, mobile, manual), extract and geolocalize Trashes and finally store the result as csv file or within PostGre Database server.

To process a gopro media without AI:
```bash
python etl.py -c gopro -b 56c76b96-6248-4723-bf1e-8674a36f8877.mp4 -p json -s gopro -t csv
```

To process a mobile media without AI:
```bash
python etl.py -c mobile -b 6250052d-f716-435c-9d71-83ad49347c5e.mp4 -p json -s mobile -t csv
```

To process a manual media without AI:
```bash
python etl.py -c manual -b 6250052d-f716-435c-9d71-83ad49347c5e.json -p json -s manual -t csv
```

Script with Parameters:
This [script](https://github.com/surfriderfoundationeurope/etl/blob/clem_dev/etl/etl.py) takes the following argument parameter: 
```bash
python etl.py -h
usage: etl.py [-h] -c CONTAINERNAME -b BLOBNAME [-a AIURL] [-p {ai,json}]
              [-s {gopro,mobile,manual}] [-t {postgre,csv}]
```

The ETL script is the foundation to build the ETL API. The ETL API relies on the ETL script logic + Azure Function to easily create a production REST API available in the Cloud.

### **Usage**

<!---TODO: It's a code block illustrating common usage that might cover basic choices that may affect usage (for instance, if JavaScript, cover promises/callbacks, ES6). If CLI importable, code block indicating both import functionality and usage (if CLI functionality exists, add CLI subsection).If relevant, point to a runnable file for the usage code.--->

<!--- These are just example (copied from current readme file): add, duplicate or remove as required --->

#### **ETL Azure Function**

After you installed [Azure function for Python pre-requesite](https://docs.microsoft.com/en-us/azure/azure-functions/functions-create-first-azure-function-azure-cli?pivots=programming-language-python&tabs=bash%2Cbrowser) on your local machine, you can run the ETL workflow as a local Azure function. 
Note you need to launch the function from within a python environment configured with ETL pre-requesite.
First go to /azfunction/etlAPIs/, then:

```bash
func start etlHttpTrigger/
```

This will run the ETL workflow as a local API using Azure function utilities.
You can therefore navigate to the ETL API endpoint using a browser, and execute the ETL process with.
Please note this will download the media file mobile.mp4 from Azure for which you need storage credential.
```
http://localhost:7071/api/etlHttpTrigger/?container=mobile&blob=6250052d-f716-435c-9d71-83ad49347c5e.mp4&prediction=json&source=mobile&target=csv
```

When the AI inference service is running you would test it by calling the API with: 
```
http://localhost:7071/api/etlHttpTrigger/?container=mobile&blob=6250052d-f716-435c-9d71-83ad49347c5e.mp4&prediction=ai&source=mobile&target=csv&aiurl=http://<AIURL>
```

When running the End to End process, download blob, making prediction with AI, writing to PostGre you would test with:
```
http://localhost:7071/api/etlHttpTrigger/?container=mobile&blob=6250052d-f716-435c-9d71-83ad49347c5e.mp4&prediction=ai&source=mobile&target=postgre&aiurl=http://<AIURL>
```

#### **ETL Trigger Azure Function**
The ETL Trigger Azure function defines additionnaly 3 x functions that will automatically call the ETL API when new media to process are stored in Azure.
They used the [blob trigger capabilities](https://docs.microsoft.com/fr-fr/azure/azure-functions/functions-bindings-storage-blob-trigger?tabs=python) defined within the [function.json](https://github.com/surfriderfoundationeurope/etl/blob/clem_dev/azfunction/etlBlobTrigger/etlBlobTriggerGoPro/function.json).
Simplest way for testing is to publish directly to Azure with:
```
func azure functionapp publish <AZUREFUNCTIONApp>
```

#### **Docker**
The GPS extraction subprocess requires to use binaries like ffmpeg which is not natively available within Python Azure Function. To address this requirement, the ETL Azure Function has been made available as a Docker image. 
The Docker file to build the image is located [here](https://github.com/surfriderfoundationeurope/etl/blob/clem_dev/azfunction/etlAPIs/Dockerfile)
You will need to pass the appropriate credential at build time for the ETL to use Azure Storage and PostGre Database server.

#### **VM Scale Set**
To overcome timeout limitation of native Azure Function service related to HTTP call and Load Balancer, the ETL APIs has also been made available to run on an Azure [Virtual Machine Scale Set](https://docs.microsoft.com/en-us/azure/virtual-machine-scale-sets/)
The related code for deployment is located [here](https://github.com/surfriderfoundationeurope/etl/tree/clem_dev/azfunction/etlAPIsVM)
To prepare the Virtual Machine for VM Scale Set deployment, the Azure related documentation can be found [here](https://docs.microsoft.com/en-us/azure/virtual-machine-scale-sets/tutorial-use-custom-image-cli)

#### **ETL Deployment Architecture**
![etlDeployment](https://user-images.githubusercontent.com/8882133/89409113-cfe4ea80-d721-11ea-9bd4-bb3899174334.png)

<!--- If needed add here any Extra Sections (must have their own titles).Specifically, the Security section should be here if it wasn't important enough to be placed above.-->

### **API references**

<!---TODO: Describe exported functions and objects. Describe signatures, return types, callbacks, and events. Cover types covered where not obvious. Describe caveats. If using an external API generator (like go-doc, js-doc, or so on), point to an external API.md file. This can be the only item in the section, if present.--->

<!--- If an external API file is work in progress, please use the text below as exaple: add, duplicate or remove as required -->
*SOON: To see API specification used by this repository browse to the Swagger documentation (currently not available).*

## **Build and Test**

<!---TODO: Describe and show how to build your code and run the tests.--->

## **Contributing**

It's great to have you here! We welcome any help and thank you in advance for your contributions.

* Feel free to **report a problem/bug** or **propose an improvement** by creating a [new issue](https://github.com/surfriderfoundationeurope/labelcv-web/issues). Please document as much as possible the steps to reproduce your problem (even better with screenshots). If you think you discovered a security vulnerability, please contact directly our [Maintainers](##Maintainers).

* Take a look at the [open issues](https://github.com/surfriderfoundationeurope/labelcv-web/issues) labeled as `help wanted`, feel free to **comment** to share your ideas or **submit a** [**pull request**](https://github.com/surfriderfoundationeurope/labelcv-web/pulls) if you feel that you can fix the issue yourself. Please document any relevant changes.

## **Maintainers**

If you experience any problems, please don't hesitate to ping:
<!--- Need to check the full list of Maintainers and their GIThub contacts -->
* [@cl3m3nt](https://github.com/cl3m3nt)

Special thanks to all our [Contributors](https://github.com/surfriderfoundationeurope/The-Plastic-Origins-Project).

## **License**

We’re using the [GNU General Public License (GPL) version 3 - `GPLv3`](https://www.gnu.org/licenses/gpl-3.0.en.html) - a free, copyleft license for software and other kinds of works.

## **Additional information**
<!--- These are just example: add, duplicate or remove as required --->
<details>
<summary>Please write here the text you would like to show</summary>

TODO: Please write here detils that you would like to hide `

</details>
