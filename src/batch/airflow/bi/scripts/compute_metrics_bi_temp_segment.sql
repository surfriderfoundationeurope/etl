DROP TABLE IF EXISTS segment_ids;
CREATE TEMP TABLE segment_ids AS
SELECT distinct bi_temp.trajectory_point_river.id_ref_segment_fk as id
FROM bi_temp.trajectory_point_river
WHERE
    id_ref_campaign_fk IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute);

TRUNCATE bi_temp.segment;
INSERT INTO bi_temp.segment(id, importance, the_geom, createdon)
SELECT
    s.id, s.importance, s.the_geom, current_timestamp
FROM referential.segment s
LEFT JOIN bi.segment bis on s.id=bis.id
WHERE s.id in (SELECT s.id from segment_ids) or bis.id is null;

-- QUERY 1: updates distance monitored and the geom monitored for segment
UPDATE bi_temp.segment
SET
    distance_monitored = st_length(
        st_intersection(s2.the_geom_monitored, s2.the_geom)
    ),
    the_geom_monitored = s2.the_geom_monitored,
    nb_campaign = s2.nb_campaign
FROM
    (
       SELECT sub.id, sub.the_geom,
            st_union(st_buffer(the_geom_monitored, 200)) as the_geom_monitored,
            count(id_ref_campaign_fk) nb_campaign
       FROM (
            SELECT
                s.id,
                tp_river.id_ref_campaign_fk,
                ST_Simplify(st_makevalid(
                    st_makeline(
                        tp_river.the_geom
                        ORDER BY tp_river.time
                    )
                ), 1, true) AS the_geom_monitored,
                s.the_geom
            FROM bi_temp.trajectory_point_river tp_river
                INNER JOIN referential.segment s ON s.id = tp_river.id_ref_segment_fk
            WHERE s.id IN (SELECT id FROM segment_ids)
            GROUP BY s.id, tp_river.id_ref_campaign_fk
        ) sub
        GROUP BY sub.id, sub.the_geom

    ) AS s2
WHERE s2.id = segment.id;

UPDATE bi_temp.segment
SET count_trash = t.count_trash,
    trash_per_km = t.count_trash / (nullif(distance_monitored, 0) / 1000)
FROM
    (
        SELECT
            tr.id_ref_segment_fk,
            count(distinct(tr.id_ref_trash_fk)) AS count_trash
        FROM bi_temp.trash_river tr
            INNER JOIN bi_temp.segment s ON s.id = tr.id_ref_segment_fk
        WHERE s.id IN (SELECT id FROM segment_ids)
        GROUP BY tr.id_ref_segment_fk

    ) AS t
WHERE t.id_ref_segment_fk = segment.id;

-- Add river data
UPDATE bi_temp.segment s
SET count_trash_river = r.count_trash,
    trash_per_km_river = r.trash_per_km,
    distance_monitored_river = r.distance_monitored,
    nb_campaign_river = r.nb_campaign
FROM (
    SELECT rs.id as segment_id, r.count_trash, r.trash_per_km, r.distance_monitored, r.nb_campaign
    FROM referential.segment rs
    INNER JOIN bi_temp.river r on r.id = rs.id_ref_river_fk
) r
WHERE s.id=r.segment_id;