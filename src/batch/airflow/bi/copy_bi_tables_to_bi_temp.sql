DROP TABLE IF EXISTS old_campaign_ids;

CREATE TEMP TABLE old_campaign_ids AS
SELECT cr.id_ref_campaign_fk
FROM bi.campaign_river cr
WHERE id_ref_campaign_fk NOT in (SELECT campaign_id FROM bi_temp.pipeline_to_compute)
;

DELETE FROM
    bi_temp.trajectory_point_river
WHERE id_ref_campaign_fk IN (SELECT id_ref_campaign_fk FROM old_campaign_ids);

INSERT INTO bi_temp.trajectory_point_river (
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
FROM bi.trajectory_point_river
WHERE
    bi.trajectory_point_river.id_ref_campaign_fk IN (
        SELECT id_ref_campaign_fk FROM old_campaign_ids
    );

DELETE FROM
    bi_temp.trash_river
WHERE id_ref_campaign_fk IN (SELECT id_ref_campaign_fk FROM old_campaign_ids);
INSERT INTO bi_temp.trash_river (
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
FROM bi.trash_river
WHERE
    bi.trash_river.id_ref_campaign_fk IN (
        SELECT id_ref_campaign_fk FROM old_campaign_ids
    );
