UPDATE bi_temp.campaign_river c
SET trash_count = trash_n.trash_count
FROM (
        SELECT
            c.id_ref_campaign_fk,
            SUM(CASE WHEN t.id IS NOT NULL THEN 1 ELSE 0 END) AS trash_count
        FROM bi_temp.campaign_river c
        LEFT JOIN bi_temp.trash_river t ON c.id_ref_campaign_fk=t.id_ref_campaign_fk
        where c.id_ref_campaign_fk IN (
            SELECT campaign_id FROM bi_temp.pipeline_to_compute
        )
        GROUP BY c.id_ref_campaign_fk

    ) AS trash_n
WHERE
    trash_n.id_ref_campaign_fk = c.id_ref_campaign_fk;

UPDATE bi_temp.campaign_river c
SET trash_per_km = c.trash_count / (nullif(c.distance, 0) / 1000);
