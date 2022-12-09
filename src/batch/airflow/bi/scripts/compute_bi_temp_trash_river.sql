-- Trash are not projected and filtered by distance on river to avoid loss of data

TRUNCATE bi_temp.trash_river;
INSERT INTO bi_temp.trash_river (
    id_ref_trash_fk,
    id_ref_campaign_fk,
    id_ref_segment_fk,
    id_ref_river_fk,
    the_geom,
    createdon
)
WITH subquery AS (
    SELECT
            t.id AS id_ref_trash_fk,
            t.id_ref_campaign_fk AS id_ref_campaign_fk,
            closest_seg.id AS id_ref_segment_fk,
            closest_seg.id_ref_river_fk AS id_ref_river_fk,
            t.the_geom AS trash_the_geom
    FROM bi_temp.trash t
    INNER JOIN bi_temp.campaign_river cr ON t.id_ref_campaign_fk=cr.id_ref_campaign_fk
    INNER JOIN lateral(
            SELECT s.id, s.id_ref_river_fk, s.importance, s.the_geom
            FROM referential.segment s
            WHERE s.id_ref_river_fk = cr.id_ref_river_fk
            ORDER BY s.the_geom <-> t.the_geom
            LIMIT 1
        ) AS closest_seg ON TRUE
    WHERE t.id_ref_campaign_fk IN (
            SELECT campaign_id FROM bi_temp.pipeline_to_compute
          )
   )
SELECT
    id_ref_trash_fk,
    id_ref_campaign_fk,
    id_ref_segment_fk,
    id_ref_river_fk,
    trash_the_geom,
    current_timestamp
FROM subquery;

DROP INDEX IF EXISTS bi_temp.trash_river_the_geom;
CREATE INDEX trash_river_the_geom
ON bi_temp.trash_river USING gist(the_geom);
