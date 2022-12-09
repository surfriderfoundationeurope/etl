CREATE TEMP TABLE trash_admin AS
SELECT
    bi_temp.trash.id,

    referential.municipality.code AS municipality_code,

    referential.municipality.name AS municipality_name,
    referential.department.code AS department_code,
    referential.department.name AS department_name,
    referential.state.code AS state_code,
    referential.state.name AS state_name,
    referential.country.code AS country_code,
    referential.country.name AS country_name
FROM
    bi_temp.trash

LEFT JOIN
    referential.municipality ON st_contains(
    referential.municipality.the_geom, bi_temp.trash.the_geom)
LEFT JOIN
    referential.department ON
        referential.department.id =
    referential.municipality.id_ref_department_fk
LEFT JOIN
    referential.state ON
        referential.state.id = referential.department.id_ref_state_fk
LEFT JOIN
    referential.country ON st_contains(
    referential.country.the_geom, bi_temp.trash.the_geom)

WHERE bi_temp.trash.id_ref_campaign_fk IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute);;

UPDATE bi_temp.trash t
SET
    municipality_code = ta.municipality_code,
    municipality_name = ta.municipality_name,
    department_code = ta.department_code,
    department_name = ta.department_name,
    state_code = ta.state_code,
    state_name = ta.state_name,
    country_code = ta.country_code,
    country_name = ta.country_name

FROM trash_admin ta
WHERE ta.id = t.id;

DROP INDEX IF EXISTS bi_temp.bi_temp_trash_geom;
CREATE INDEX bi_temp_trash_geom ON bi_temp.trash using gist(the_geom);
