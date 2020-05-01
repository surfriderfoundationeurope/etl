select id_ref_campaign_fk ,sum(elevation) from public.trash group by (id_ref_campaign_fk)
