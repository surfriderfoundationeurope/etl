UPDATE bi_temp.campaign c
SET the_geom = points.the_geom
FROM (
    SELECT id_ref_campaign_fk,
        ST_Simplify(st_makevalid(
            st_makeline(
                tp.the_geom
                ORDER BY tp.time
            )
        ), 1, true) the_geom
    FROM bi_temp.trajectory_point tp
    WHERE id_ref_campaign_fk IN (
        SELECT campaign_id FROM bi_temp.pipeline_to_compute
    )
    GROUP BY id_ref_campaign_fk
) points
WHERE points.id_ref_campaign_fk=c.id;

UPDATE bi_temp.campaign c
SET start_date = point.min_time,
    end_date = point.max_time,
    duration = age(point.max_time, point.min_time)

FROM (
        SELECT

            id_ref_campaign_fk,
            min(time) AS min_time,
            max(time) AS max_time

        FROM campaign.trajectory_point
        GROUP BY id_ref_campaign_fk

    ) AS point

WHERE
    point.id_ref_campaign_fk = c.id AND c.id IN (
        SELECT campaign_id FROM bi_temp.pipeline_to_compute
    );

UPDATE bi_temp.campaign c
SET start_point = start_geom.the_geom
FROM bi_temp.trajectory_point AS start_geom
WHERE
    start_geom.id_ref_campaign_fk = c.id AND start_geom.time = c.start_date AND c.id IN (
        SELECT campaign_id FROM bi_temp.pipeline_to_compute
    );

UPDATE bi_temp.campaign c
SET end_point = end_geom.the_geom
FROM bi_temp.trajectory_point AS end_geom
WHERE
    end_geom.id_ref_campaign_fk = c.id AND end_geom.time = c.end_date AND c.id IN (
        SELECT campaign_id FROM bi_temp.pipeline_to_compute
    );

UPDATE bi_temp.campaign c
SET distance = agg.distance,
    avg_speed = agg.avg_speed
FROM (
    SELECT
        id_ref_campaign_fk,
        sum(distance) AS distance,
        avg(speed) AS avg_speed
    FROM bi_temp.trajectory_point
    WHERE distance > 0
    GROUP BY id_ref_campaign_fk
    ) AS agg
WHERE
    agg.id_ref_campaign_fk = c.id AND c.id IN (
        SELECT campaign_id FROM bi_temp.pipeline_to_compute
    );


UPDATE bi_temp.campaign c
SET trash_count = trash_n.trash_count,
    createdon = current_timestamp
FROM (
        SELECT
            id_ref_campaign_fk,
            count(*) AS trash_count
        FROM bi_temp.trash
        GROUP BY id_ref_campaign_fk

    ) AS trash_n

WHERE
    trash_n.id_ref_campaign_fk = c.id AND c.id IN (
        SELECT campaign_id FROM bi_temp.pipeline_to_compute
    );

UPDATE bi_temp.campaign c
SET trash_per_km = c.trash_count / (nullif(c.distance, 0) / 1000);
