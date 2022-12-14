DROP TABLE IF EXISTS river_ids;
CREATE TEMP TABLE river_ids AS
SELECT distinct bi_temp.trajectory_point_river.id_ref_river_fk as id
FROM bi_temp.trajectory_point_river
WHERE
    id_ref_campaign_fk IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute);

TRUNCATE bi_temp.river;
INSERT INTO bi_temp.river(id, name, importance, the_geom, createdon)
SELECT
    r.id, r.name, r.importance, r.the_geom, current_timestamp
FROM referential.river r
LEFT JOIN bi.river bir on bir.id=r.id
WHERE r.id in (SELECT id from river_ids) or bir.id is null;


-- QUERY 1: updates distance monitored and the geom monitored for river
UPDATE bi_temp.river
SET
    distance_monitored = st_length(
        st_intersection(r2.the_geom_monitored, r2.the_geom)
    ),
    the_geom_monitored = r2.the_geom_monitored,
    nb_campaign = r2.nb_campaign
FROM
    (
        SELECT sub.id, sub.the_geom,
            st_union(st_buffer(the_geom_monitored, 200)) AS the_geom_monitored,
            count(id_ref_campaign_fk) nb_campaign
        FROM (
            SELECT
                r.id,
                tp_river.id_ref_campaign_fk,
                ST_Simplify(st_makevalid(
                    st_makeline(
                        tp_river.the_geom
                        ORDER BY tp_river.time
                    )
                ), 1, true) AS the_geom_monitored,
                r.the_geom
            FROM bi_temp.trajectory_point_river tp_river
                INNER JOIN referential.river r ON r.id = tp_river.id_ref_river_fk
            WHERE r.id IN (SELECT id FROM river_ids)
            GROUP BY r.id, tp_river.id_ref_campaign_fk
        ) sub
        GROUP BY sub.id, sub.the_geom
    ) AS r2
WHERE r2.id = river.id;

UPDATE bi_temp.river
SET count_trash = t.count_trash,
    trash_per_km = t.count_trash / (nullif(distance_monitored, 0) / 1000)
FROM
    (
        SELECT
            tr.id_ref_river_fk,
            count(distinct(tr.id_ref_trash_fk)) AS count_trash
        FROM bi_temp.trash_river tr
            INNER JOIN bi_temp.river r ON r.id = tr.id_ref_river_fk
        WHERE r.id IN (SELECT id FROM river_ids)
        GROUP BY tr.id_ref_river_fk

    ) AS t
WHERE t.id_ref_river_fk = river.id;
