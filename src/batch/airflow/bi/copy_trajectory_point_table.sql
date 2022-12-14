DELETE FROM bi_temp.trajectory_point
WHERE id_ref_campaign_fk IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute);
INSERT INTO bi_temp.trajectory_point (
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
    NULL::int,
    NULL::interval,
    "time",
    speed,
    st_y(st_transform(ST_SetSRID(the_geom, 2154), 4326)),
    st_x(st_transform(ST_SetSRID(the_geom, 2154), 4326)),
    createdon

FROM campaign.trajectory_point
WHERE
    id_ref_campaign_fk IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute) AND the_geom IS NOT NULL;

INSERT INTO bi_temp.trajectory_point (
    id,
    the_geom,
    id_ref_campaign_fk,
    elevation,
    distance,
    time_diff,
    "time",
    speed,
    lat,
    lon,
    createdon

)
SELECT
    id,
    st_transform(ST_SetSRID(ST_MakePoint(lon, lat), 4326),2154),
    id_ref_campaign_fk,
    elevation,
    NULL::int,
    NULL::interval,
    "time",
    speed,
    lat,
    lon,
    createdon

FROM campaign.trajectory_point
WHERE
    id_ref_campaign_fk IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute)
    AND lon IS NOT NULL AND lat IS NOT NULL AND the_geom IS NULL;

DROP INDEX IF EXISTS bi_temp.trajectory_point_the_geom;
CREATE INDEX trajectory_point_the_geom on bi_temp.trajectory_point using gist(the_geom);
