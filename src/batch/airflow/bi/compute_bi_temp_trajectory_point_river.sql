TRUNCATE bi_temp.trajectory_point_river;

-- Trajectory points are projected on the river closest to the entire campaign

INSERT INTO bi_temp.trajectory_point_river (
    id_ref_trajectory_point_fk,
    id_ref_campaign_fk,
    id_ref_segment_fk,
    id_ref_river_fk,
    the_geom,
    time,
    createdon
)

WITH subquery_1 AS (

    SELECT
        tp.id AS id_ref_trajectory_point_fk,
        tp.id_ref_campaign_fk,
        closest_seg.id AS id_ref_segment_fk,
        closest_seg.id_ref_river_fk AS id_ref_river_fk,
        tp.the_geom AS trajectory_point_the_geom,
        st_closestpoint(closest_seg.the_geom, tp.the_geom) AS closest_point_the_geom,
        tp.time
    FROM (
            SELECT DISTINCT ON (tp.id_ref_campaign_fk) id_ref_campaign_fk,
                closest_seg.id_ref_river_fk
            FROM bi_temp.trajectory_point tp
                INNER JOIN lateral(
                    SELECT s.id, s.id_ref_river_fk, s.the_geom
                    FROM referential.segment s
                    ORDER BY s.the_geom <-> tp.the_geom
                    LIMIT 1
                ) AS closest_seg ON TRUE
            WHERE
                tp.id_ref_campaign_fk IN (
                    SELECT campaign_id FROM bi_temp.pipeline_to_compute
                )
            GROUP BY tp.id_ref_campaign_fk, closest_seg.id_ref_river_fk
            ORDER BY tp.id_ref_campaign_fk, count(*) DESC
        ) closest_river
        INNER JOIN bi_temp.trajectory_point tp ON tp.id_ref_campaign_fk=closest_river.id_ref_campaign_fk
        INNER JOIN lateral(
            SELECT s.id, s.id_ref_river_fk, s.the_geom
            FROM referential.segment s
            WHERE s.id_ref_river_fk=closest_river.id_ref_river_fk
            ORDER BY s.the_geom <-> tp.the_geom
            LIMIT 1
        ) AS closest_seg ON TRUE
)

SELECT
    id_ref_trajectory_point_fk,
    id_ref_campaign_fk,
    id_ref_segment_fk,
    id_ref_river_fk,
    closest_point_the_geom,
    time,
    current_timestamp
FROM subquery_1
WHERE st_distance(closest_point_the_geom, trajectory_point_the_geom) < 500;

DROP INDEX IF EXISTS bi_temp.trajectory_point_river_the_geom;

CREATE INDEX trajectory_point_river_the_geom
ON bi_temp.trajectory_point_river USING gist(the_geom);
