UPDATE campaign.campaign
SET has_been_computed = TRUE
WHERE id IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute);

UPDATE bi_temp.pipelines
SET campaign_has_been_computed = TRUE,
    river_has_been_computed = TRUE
WHERE
    campaign_id IN (SELECT campaign_id FROM bi_temp.pipeline_to_compute);


