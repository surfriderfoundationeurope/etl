TRUNCATE bi_temp.campaign;
INSERT INTO bi_temp.campaign (
    id,
    locomotion,
    isaidriven,
    remark,
    id_ref_user_fk,
    riverside,
    createdon
)
SELECT
    id,
    locomotion,
    isaidriven,
    remark,
    id_ref_user_fk,
    riverside,
    createdon
FROM campaign.campaign
WHERE id IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute);