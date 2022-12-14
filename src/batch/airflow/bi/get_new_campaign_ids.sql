INSERT INTO bi_temp.pipelines (campaign_id)
SELECT id
FROM campaign.campaign
WHERE
    has_been_computed IS NULL
    AND id NOT IN (SELECT campaign_id FROM bi_temp.pipelines);

DROP VIEW IF EXISTS bi_temp.pipeline_to_compute;
CREATE VIEW bi_temp.pipeline_to_compute AS
SELECT campaign_id
FROM bi_temp.pipelines
WHERE campaign_has_been_computed IS NULL AND river_has_been_computed IS NULL
;
