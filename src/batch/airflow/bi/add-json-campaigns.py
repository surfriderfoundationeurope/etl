import logging
from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.utils.dates import days_ago
from airflow.decorators import task
from airflow.models.param import Param
from postgre import get_pg_connection_string, open_pg_connection, close_pg_connection

import uuid
from datetime import datetime


doc_md_DAG = """
## Add JSON Campaigns


This DAG enables to add campaigns directly from a json file of a user. It is typically used when there was an error with
data within the mobile App or API.
It does what the mobile API normally does. You still have to run the etl and bi-pipeline to finalise adding the data to the database 

### Running this DAG 

- Find the user you want to add the campaign to, by looking at the `campaign.user` database, and noting the `[userID]`
- Open the json file and copy the id in it (it looks like: ace36cf3-0170-45d7-b5f0-e45aaee2148c / first line of the json). Rename the file from `trace_14-07-2023_16h05.json` to `[id].json`. Be careful, this campaign id is different from `[userID]`!  
- Upload the Json file in the manual container. A notification informs you that the file has been added, checking that it was not already in the container. 

Then trigger the DAG:
- When triggerin the DAG, select "Run with parameters":
- Copy the contents of the JSON file
- Replace the json content by pasting your own JSON  
- just after the first bracket '{', add the user: "user": "[userID]" 
- click `Trigger` 
--

#### How it works

- It creates a line in `campaign.campaign`
- It creates lines in `campaign.trajectory_points`

#### If it fails
- Verify in the database that the campaign is not present before re-running this DAG

#### Maintainers
- Charles Ollion or Clément Le Roux
"""

logger = logging.getLogger()

with DAG(

    dag_id= 'add-json-campaigns',
    start_date=days_ago(1),
    schedule_interval=None,
    catchup=False,
    doc_md=doc_md_DAG,
    params={
        "user": Param("[userID]", type="string"),
        "id": Param("ace36cf3-0170-45d7-b5f0-e45aaee2148c", type="string"),
        "date":Param("2023-09-23T11:10:30.033Z", type="string"),
        "duration":Param(50, type="integer"),
        "move":Param("kayak", type="string"),
        "bank":Param("rightBank", type="string"),
        "trackingMode":Param("manual", type="string"),
        "files":Param([], type="array"),
        "trashes":Param([],type="array"),
        "positions":Param([], type="array"),
        "comment": Param("", type="string"),
        "isStarted": Param(False, type="boolean"),
        "isFinished": Param(False, type="boolean"),
        "isSynced": Param(False, type="boolean"),
    }

) as dag:
# Parameters

    # PG connection
    pg_conn_string = get_pg_connection_string()
    pg_connection = open_pg_connection(pg_conn_string)
    #pg_cursor = pg_connection.cursor()
    

    # [START add_json_campaign]
    @task(task_id="add_json_campaign")
    
    def add_json_campaign(pg_connection, **context):
        data = context["params"]
        campaign_query = """
            INSERT INTO campaign.campaign (id, locomotion, isaidriven, remark, id_ref_user_fk, riverside, createdon)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        campaign_values = (
            data['id'],
            data['move'],
            "true" if data['trackingMode'] == "automatic" else "false",
            data['comment'],
            data['user'], 
            "right" if data['bank']=="rightBank" else "left",
            data['date']
        )
        trajectory_query = """
            INSERT INTO campaign.trajectory_point (id, id_ref_campaign_fk, "time", lat, lon, createdon)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        createdon = datetime.now()
        with pg_connection.cursor() as cursor:
            
            cursor.execute(campaign_query, campaign_values)
            campaign_id = uuid.UUID(data['id'])

            for position in data['positions']:
                trajectory_values = (
                    str(uuid.uuid4()),
                    data['id'],
                    position['date'],
                    position['lat'],
                    position['lng'],
                    str(createdon)
                )
                cursor.execute(trajectory_query, trajectory_values)
        
        pg_connection.commit()
        pg_connection.close()

        return None

    add_json_campaign_op = add_json_campaign(pg_connection)
    # [END add_json_campaign]

