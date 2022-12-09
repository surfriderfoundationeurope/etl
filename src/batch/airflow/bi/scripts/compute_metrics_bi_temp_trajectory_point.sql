DROP TABLE IF EXISTS trajectory_point_agg;
CREATE TEMP TABLE trajectory_point_agg AS
SELECT

    id,
    st_distance(
        the_geom,
        lag(the_geom) OVER( PARTITION BY id_ref_campaign_fk ORDER BY time ASC )
    ) AS distance,
    age(
        "time",
        lag("time") OVER( PARTITION BY id_ref_campaign_fk ORDER BY time ASC )
    ) AS time_diff

FROM bi_temp.trajectory_point
WHERE
    id_ref_campaign_fk IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute);

UPDATE bi_temp.trajectory_point t
SET
    distance = agg.distance,
    time_diff = agg.time_diff

FROM trajectory_point_agg AS agg
WHERE agg.id = t.id;

UPDATE bi_temp.trajectory_point
SET speed = (distance / extract(epoch FROM time_diff)) * 3.6
WHERE speed IS NULL
    AND extract(epoch FROM time_diff) > 0
    AND distance > 0
    AND id_ref_campaign_fk IN (
        SELECT campaign_id FROM bi_temp.pipeline_to_compute
    );

DROP INDEX IF EXISTS bi_temp.bi_temp_trajectory_point;
CREATE INDEX bi_temp_trajectory_point ON bi_temp.trajectory_point USING GIST(the_geom);
