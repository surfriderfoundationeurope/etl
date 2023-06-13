DELETE FROM
    bi_temp.campaign_river
WHERE
    id_ref_campaign_fk IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute);
INSERT INTO bi_temp.campaign_river (
    id_ref_campaign_fk,
    id_ref_river_fk,
    the_geom,
    distance,
    createdon
)
WITH subquery_1 AS (

    SELECT
        id_ref_campaign_fk,
        id_ref_river_fk,
        ST_Simplify(st_makevalid(
            st_makeline(
                the_geom
                ORDER BY time
            )
        ), 1, true) AS the_geom
    FROM bi_temp.trajectory_point_river
    WHERE id_ref_campaign_fk IN (
        SELECT campaign_id FROM bi_temp.pipeline_to_compute
    )
    GROUP BY id_ref_campaign_fk, id_ref_river_fk

)

SELECT DISTINCT ON (id_ref_campaign_fk, id_ref_river_fk)
    id_ref_campaign_fk,
    id_ref_river_fk,
    the_geom,
    st_length(the_geom) AS distance,
    current_timestamp
FROM
    subquery_1

ORDER BY id_ref_campaign_fk, id_ref_river_fk, st_length(the_geom) DESC;

-- Add the tag disabled to campaigns with GPS problems. They are identified when the number of  
-- trash is 8 times below the number of different trash locations
WITH table_summary AS (
    WITH grouped_trash AS (
        SELECT 
            id_ref_campaign_fk, 
            the_geom, 
            count(*) AS num, 
            -- MAX("time") AS time2 
        FROM bi.trash
        WHERE id_ref_campaign_fk IN (
            SELECT campaign_id FROM bi_temp.pipeline_to_compute
        )
        GROUP BY id_ref_campaign_fk, the_geom

    )
    SELECT 
        id_ref_campaign_fk, 
        count(*) AS "num different locations", 
        sum(num) AS "num trash", 
        -- MAX(time2) AS "time" 
    FROM grouped_trash 
    GROUP BY id_ref_campaign_fk
)
UPDATE bi_temp.campaign_river cr 
SET "disabled" = TRUE
WHERE cr.id_ref_campaign_fk IN (
    SELECT id_ref_campaign_fk 
    FROM table_summary ts 
    WHERE (ts."num trash" > ts."num different locations" * 8)
)

DROP INDEX IF EXISTS bi_temp.campaign_river_the_geom;

CREATE INDEX campaign_river_the_geom
ON bi_temp.campaign_river USING gist(the_geom);
