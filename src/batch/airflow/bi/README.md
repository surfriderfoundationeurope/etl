## Plastic-Origin - Airflow Pipelines 

This Airflow Pipeline must be used to compute metrics of `BI` schema in `PlasticOrigin` database

## Requirements

- [Apache-Airflow](https://airflow.apache.org/docs/apache-airflow/stable/start/docker.html), easier ton install localy using docker-compose ;) 

- Creates connection to database (env `dev`or `prod`) 

  ```bash
  ./airflow.sh connections add [CONNECTIO] --conn-uri 'postgres://[USERNAME]@pgdb-plastico-dev:[PASSWORD]@pgdb-plastico-[ENV].postgres.database.azure.com:5432/plastico-[ENV]'
  ```



## Pipeline description

The main purpose of this pipeline is to compute Plastic-Origin metrics that will be available on Plastic-Origin website. 

We have choosen to perform metrics computation using SQL engine (Postgres backend) as the data processing requires Postgis framework (geospatial processing). Postgis offers a wide range of predefined functions to manipulate geospatial datatype: 

- geometry projection (`ST_TRANSFORM`, `ST_SETSRID` ...)

- distance calculation  (`ST_DISTANCE`, `<->`, `ST_CLOSESTPOINT`)

- polygon processing (`ST_SIMPLIFY`)

  

  Current PO database relies on 3 schema: 

- Campaign > campaign raw data stored (trash geometry, trajectory point, users informations, campaign ... ). It is enriched by `AI-ETL`.
- BI > aggregated metrics fetched by Plastic-Origin backend API. 
- BI_TEMP > temporary schema to compute metrics 

The needs of a temporary schema can be challenged, but we needed to make sur data pipeline is atomic, and in case of failure won't corrupt productions datasets.  


#Bi-Reset Campaign

`has_been_computed` is set to NULL column  to identify all campaigns as new and to process.


## Bi-Pipeline


### Step 1 - Identify new campaigns to process

All campaigns are stored in `campaign.campaign` tables, id column as a unique identifier. 

`has_been_computed` is a default NULL column and is used by our program to identify new campaign to process.

This step is managed by task `get_new_campaign_ids` 

### Step2 - Copy campaign data 

New campaigns data are copied from the `campaign`  schema to the `bi_temp`. 

Tables concerned - `trash`, `trajectory_point`, `campaign`

This step is managed by tasks `copy_campaign_table`, `copy_trash_table`, `copy_trajectory_point_table`

### Step3 - Compute metrics 

Then a set is metric is compute for the following tables: 

For trajectory-point table: 

- `distance` with previous trajectory point.

- `time_diff` with the previous trajectory point.

- `speed` > computed as `distance/time_diff*3.6`

  
  For trash table: 

each trash is associated to its locality: `department`, `municipality`,  `state`,`country` 

This step is managed by tasks `compute_metrics_bi_temp_trajectory_point`, `compute_metrics_bi_temp_trash`


### Step4 - Compute campaign/trajectory point/trash - river/segment association

Then, we associate each trajectory point of the `bi_temp` schema with a geom, to the `river`  referential 
and the `segment` referential.
Trajectory points are projected on the river closest to the entire campaign using `ST_CLOSESTPOINT `function (postgis)
and linked to the closest `segment` of the chosen river. 

We have decided to not associate trajectory point to a river, if the distance to its closest point is over 500m.

This step is managed by tasks : `compute_bi_temp_trajectory_point_river.sql`


Then for each campaign, campaign geometry (`the_geom`) on referential river is computed and its distance.

This step is managed by task :`compute_bi_temp_campaign_river.sql`  


Then for each trash, we associate the river of the campaign and the closest segment of the river.
This step is managed by task :`compute_bi_temp_trash_river.sql`  



### Step5 - Compute campaign metrics

For campaign table: 

- campaign `start_date` : first timestamp of the campaign in the trajectory point table.

- campaign `end_date`: last timstamp of the campaign i the trajectory point table

- campaign `duration`: difference between `end_date`and `start_date`

- campaign `starting_point`and `ending_point` : point associated with `start_date`and `end_date`

- Total distance of the campaign: sum of `distance` in the trajectory point table, of the campaign

- Average speed, average of `speed` in the trajectory point table, of the campaign 

- number of trash detected during the campaign `trash_count`, from `trash` table

- trash per km : trash count / total distance

This step is managed by task `compute_metrics_bi_temp_campaign.sql`


### Step6 - Add metrics for  campaign river
For campaign river table:
- trash per km: trash count  / total distance of the campaign projected on the river
This step is managed by task `add_metrics_bi_temp_campaign_river.sql`


### Step7 - Data copy from BI to BI_TEMP

Before re-computing metrics on rivers with newly ingested campaign, we need to gather the all data history. 

For the following tables, data are migrated from bi schema to bi_temp: `campaign_river`, `trash_river`

This step is managed by task: `copy_bi_tables_to_bi_temp.sql`

### Step8 - Compute metrics on rivers

The following metrics are computed for each river: 

- `distance_monitored` distance monitored by campaign (computed on river geometry), null if `the_geom_monitored` is null 
- `the_geom_monitored` (geometry of recorded campaigns)
- - `nb_campaign` (number of campaigns on the river)
- `count_trash` (number of trash detected on the river)
- `trash_per_km` (number of trash detected on the river by km), null if `count_trash` = 0 

This step is managed by task: `compute_metrics_bi_temp_river.sql`


### Step9 - Compute metrics on segments of river

The following metrics are computed for each segment of river: 

- `distance_monitored` distance monitored by campaign (computed on segment geometry), null if `the_geom_monitored` is null 
- `the_geom_monitored` (geometry of recorded campaigns)
- `nb_campaign` (number of campaign on the segment)
- `count_trash` (number of trash detected on the segment)
- `trash_per_km` (number of trash detected on the segment by km), null if `count_trash` = 0 

The following metrics are retrieved from bi_temp.river:
count_trash_river, trash_per_km_river, distance_monitored_river, nb_campaign_river

This step is managed by task: `compute_metrics_bi_temp_segment.sql`

### Step10 -  BI Data updating, Cleaning and Logging

Once all metrics have been computed, data can be safely updated in the `BI` schema. 

1. All newly computed data are migrated to the `BI` schema 
2. For the successfully processed campaign: 
   - set `has_been_computed`to `True` in `campaign.campaign`
   - set `campaign_has_been_computed` and `river_has_been_computed`to `True` in `bi_temp.pipelines` 

This step is managed by tasks: `update_bi_tables.sql`, `log_status_pipeline.sql`



## BI-postprocessing DAG

Generate feature collections for bi.segment, bi.river, bi.trash_river