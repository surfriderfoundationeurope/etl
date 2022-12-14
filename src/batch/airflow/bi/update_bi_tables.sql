DELETE FROM
    bi.campaign
WHERE id IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute);
INSERT INTO bi.campaign (
    id,
    locomotion,
    isaidriven,
    remark,
    id_ref_user_fk,
    riverside,
    start_date,
    end_date,
    start_point,
    end_point,
    distance,
    avg_speed,
    duration,
    trash_count,
    trash_per_km,
    id_ref_model_fk,
    the_geom,
    createdon
)
SELECT
    id,
    locomotion,
    isaidriven,
    remark,
    id_ref_user_fk,
    riverside,
    start_date,
    end_date,
    start_point,
    end_point,
    distance,
    avg_speed,
    duration,
    trash_count,
    trash_per_km,
    id_ref_model_fk,
    the_geom,
    createdon
FROM bi_temp.campaign
WHERE id IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute);

DELETE FROM
    bi.campaign_river
WHERE
    id_ref_campaign_fk IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute);
INSERT INTO bi.campaign_river (
    id,
    id_ref_campaign_fk,
    id_ref_river_fk,
    distance,
    trash_count,
    trash_per_km,
    the_geom,
    createdon
)
SELECT
    id,
    id_ref_campaign_fk,
    id_ref_river_fk,
    distance,
    trash_count,
    trash_per_km,
    the_geom,
    createdon
FROM bi_temp.campaign_river
WHERE
    id_ref_campaign_fk IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute)
ORDER BY id_ref_campaign_fk ASC, distance DESC;

DROP INDEX IF EXISTS bi.campaign_river_the_geom;
CREATE INDEX campaign_river_the_geom
ON bi.campaign_river USING gist(the_geom);


DELETE FROM
    bi.trajectory_point
WHERE
    id_ref_campaign_fk IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute);
INSERT INTO bi.trajectory_point (
    id,
    the_geom,
    id_ref_campaign_fk,
    elevation,
    distance,
    time_diff,
    time,
    speed,
    lat,
    lon,
    createdon
)
SELECT
    id,
    the_geom,
    id_ref_campaign_fk,
    elevation,
    distance,
    time_diff,
    time,
    speed,
    lat,
    lon,
    createdon
FROM bi_temp.trajectory_point
WHERE
    id_ref_campaign_fk IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute);

-- QUERY 4: migration for table trajectory_point_river
DELETE FROM
    bi.trajectory_point_river
WHERE
    id_ref_campaign_fk IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute);
INSERT INTO bi.trajectory_point_river (
    id,
    id_ref_trajectory_point_fk,
    id_ref_campaign_fk,
    id_ref_segment_fk,
    id_ref_river_fk,
    the_geom,
    time,
    createdon
)
SELECT
    id,
    id_ref_trajectory_point_fk,
    id_ref_campaign_fk,
    id_ref_segment_fk,
    id_ref_river_fk,
    the_geom,
    time,
    createdon
FROM bi_temp.trajectory_point_river
WHERE
    id_ref_campaign_fk IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute);

DELETE FROM
    bi.trash
WHERE
    id_ref_campaign_fk IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute);
INSERT INTO bi.trash (
    id,
    id_ref_campaign_fk,
    the_geom,
    elevation,
    id_ref_trash_type_fk,
    precision,
    id_ref_model_fk,
    time,
    lat,
    lon,
    municipality_code,
    municipality_name,
    department_code,
    department_name,
    state_code,
    state_name,
    country_code,
    country_name,
    createdon
)
SELECT
    id,

    id_ref_campaign_fk,
    the_geom,
    elevation,
    id_ref_trash_type_fk,
    precision,
    id_ref_model_fk,
    time,
    lat,
    lon,
    municipality_code,
    municipality_name,
    department_code,
    department_name,
    state_code,
    state_name,
    country_code,
    country_name,
    createdon
FROM bi_temp.trash
WHERE
    id_ref_campaign_fk IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute);

-- QUERY 6: migration for table trash_river
DELETE FROM
    bi.trash_river
WHERE
    id_ref_campaign_fk IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute);
INSERT INTO bi.trash_river (
    id,
    id_ref_trash_fk,
    id_ref_campaign_fk,
    id_ref_segment_fk,
    id_ref_river_fk,
    the_geom,
    createdon
)
SELECT
    id,

    id_ref_trash_fk,
    id_ref_campaign_fk,
    id_ref_segment_fk,
    id_ref_river_fk,
    the_geom,
    createdon
FROM bi_temp.trash_river
WHERE
    id_ref_campaign_fk IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute);
DROP INDEX IF EXISTS bi.trash_river_the_geom;
CREATE INDEX trash_river_the_geom
ON bi.trash_river USING gist(the_geom);

-- QUERY 7 : Migration for table river
DELETE FROM bi.river
WHERE id IN  (SELECT id from bi_temp.river);

INSERT INTO bi.river (
    id,
    name,
    importance,
    count_trash,
    distance_monitored,
    the_geom_monitored,
    trash_per_km,
    nb_campaign,
    the_geom,
    createdon
)
SELECT
    id,
    name,
    importance,
    count_trash,
    distance_monitored,
    the_geom_monitored,
    trash_per_km,
    nb_campaign,
    the_geom,
    createdon
FROM bi_temp.river;

DROP INDEX IF EXISTS bi.river_the_geom;

CREATE INDEX river_the_geom
ON bi.river USING gist(the_geom);

-- QUERY 8 : Migration for table segment
DELETE FROM bi.segment
WHERE id IN  (SELECT id from bi_temp.segment);

INSERT INTO bi.segment (
    id,
    importance,
    count_trash,
    distance_monitored,
    trash_per_km,
    nb_campaign,
    count_trash_river,
    distance_monitored_river,
    trash_per_km_river,
    nb_campaign_river,
    the_geom_monitored,
    the_geom,
    createdon
)
SELECT
    id,
    importance,
    count_trash,
    distance_monitored,
    trash_per_km,
    nb_campaign,
    count_trash_river,
    distance_monitored_river,
    trash_per_km_river,
    nb_campaign_river,
    the_geom_monitored,
    the_geom,
    createdon
FROM bi_temp.segment;

DROP INDEX IF EXISTS bi.segment_the_geom;

CREATE INDEX segment_the_geom
ON bi.segment USING gist(the_geom);
