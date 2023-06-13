-- Clean all "disabled tags"
UPDATE bi.campaign_river SET "disabled" = NULL;

-- Add the tag disabled to campaigns with GPS problems. They are identified when the number of  
-- trash is 8 times below the number of different trash locations
WITH table_summary AS (
    WITH grouped_trash AS (
        SELECT 
            id_ref_campaign_fk, 
            the_geom, 
            count(*) AS num, 
            MAX("time") AS time2 
        FROM bi.trash
        GROUP BY id_ref_campaign_fk, the_geom
    )
    SELECT 
        id_ref_campaign_fk, 
        count(*) AS "num different locations", 
        sum(num) AS "num trash", 
        max(time2) AS "time" 
    FROM grouped_trash 
    GROUP BY id_ref_campaign_fk
)
UPDATE bi.campaign_river cr 
SET "disabled" = TRUE
WHERE cr.id_ref_campaign_fk IN (
    SELECT id_ref_campaign_fk 
    FROM table_summary ts 
    WHERE (ts."num trash" > ts."num different locations" * 8)
)
