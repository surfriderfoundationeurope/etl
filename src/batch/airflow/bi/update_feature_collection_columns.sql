update bi.segment bis
set feature_collection  = json_build_object(
    'type', 'Feature', 'geometry', st_asgeojson(st_transform(ST_SetSRID(s2.the_geom, 2154), 4326)) :: json,
    'properties', s2.properties)
FROM (
    select rs.id, rs.the_geom,
        json_strip_nulls (row_to_json(segment_properties)) as properties
    FROM (
        SELECT bis.id, rs.code as code,
             bis.trash_per_km, bis.distance_monitored,
             bis.nb_campaign, trash.trashes_by_type,
             rs.importance,
             JSON_BUILD_OBJECT(
                'id', rr.id,
				 'code', rr.code,
                'name', rr.name,
                'trash_per_km',  bir.trash_per_km,
                'distance_monitored', bir.distance_monitored,
                'nb_campaign', bir.nb_campaign,
                'trashes_by_type',  trash_river.trashes_by_type
             ) AS river
        FROM bi.segment bis
            INNER JOIN referential.segment rs on rs.id=bis.id
            LEFT JOIN referential.river rr on rr.id=rs.id_ref_river_fk
            LEFT JOIN bi.river bir on bir.id = rr.id
            LEFT JOIN (
                SELECT id_ref_segment_fk,
                    ARRAY_AGG(JSON_BUILD_OBJECT(COALESCE(name, 'no_type') , nb_trash)) trashes_by_type
                FROM(
                    SELECT tr.id_ref_segment_fk, tt.name, count(tr.id) nb_trash
                    FROM bi.trash_river tr
                    LEFT JOIN bi.trash t on t.id=tr.id_ref_trash_fk
                    LEFT JOIN campaign.trash_type tt on tt.id=t.id_ref_trash_type_fk
                    GROUP BY tr.id_ref_segment_fk, tt.name
                ) sub
                GROUP BY id_ref_segment_fk
            ) trash ON trash.id_ref_segment_fk = bis.id
            LEFT JOIN (
                SELECT id_ref_river_fk,
                    ARRAY_AGG(JSON_BUILD_OBJECT(COALESCE(name, 'no_type') , nb_trash)) trashes_by_type
                FROM(
                    SELECT tr.id_ref_river_fk, tt.name, count(tr.id) nb_trash
                    FROM bi.trash_river tr
                    LEFT JOIN bi.trash t on t.id=tr.id_ref_trash_fk
                    LEFT JOIN campaign.trash_type tt on tt.id=t.id_ref_trash_type_fk
                    GROUP BY tr.id_ref_river_fk, tt.name
                ) sub
                GROUP BY id_ref_river_fk
            ) trash_river ON trash_river.id_ref_river_fk = bir.id
    ) segment_properties
    LEFT JOIN referential.segment rs on rs.id=segment_properties.id
) s2
WHERE s2.id = bis.id;


update bi.river bir
set feature_collection  = json_build_object(
    'type', 'Feature', 'geometry', st_asgeojson(st_transform(ST_SetSRID(r2.the_geom, 2154), 4326)) :: json,
    'properties', r2.properties)
FROM (
    select rr.id, rr.the_geom,
        json_strip_nulls (row_to_json(river_properties)) as properties
    FROM (
        SELECT rr.id, rr.code, rr.name, rr.importance,
            bir.trash_per_km, bir.distance_monitored,
            bir.nb_campaign, trash.trashes_by_type
        FROM bi.river bir
            INNER JOIN referential.river rr on rr.id=bir.id
            LEFT JOIN (
                SELECT id_ref_river_fk,
                    ARRAY_AGG(JSON_BUILD_OBJECT(COALESCE(name, 'no_type'), nb_trash)) trashes_by_type
                FROM(
                    SELECT tr.id_ref_river_fk, tt.name, count(tr.id) nb_trash
                    FROM bi.trash_river tr
                    LEFT JOIN bi.trash t on t.id=tr.id_ref_trash_fk
                    LEFT JOIN campaign.trash_type tt on tt.id=t.id_ref_trash_type_fk
                    GROUP BY tr.id_ref_river_fk, tt.name
                ) sub
                GROUP BY id_ref_river_fk
            ) trash ON trash.id_ref_river_fk = bir.id
    ) river_properties
    LEFT JOIN referential.river rr on rr.id=river_properties.id
) r2
WHERE r2.id = bir.id;

UPDATE bi.trash_river t
SET feature_collection=json_build_object(
    'type', 'Feature', 'geometry', st_asgeojson(st_transform(ST_SetSRID(t2.the_geom, 2154), 4326)) :: json,
    'properties', t2.properties)
FROM (
    SELECT tr.id, tr.the_geom,
        json_strip_nulls (row_to_json(trash_properties)) as properties
    FROM (
        SELECT tr.id, t.id as trash_id, t_type.id as type_id, t_type.name as type_name,
            t.time, t.id_ref_campaign_fk, c.isaidriven, u.firstname,
            r.id as river_id, r.code as river_code, r.name as river_name
        FROM bi.trash_river tr
            LEFT JOIN bi.trash t ON t.id=tr.id_ref_trash_fk
            LEFT JOIN campaign.trash_type t_type ON t_type.id=t.id_ref_trash_type_fk
            LEFT JOIN campaign.campaign c ON c.id=t.id_ref_campaign_fk
            LEFT JOIN campaign.user u ON u.id=c.id_ref_user_fk
            LEFT JOIN referential.river r ON r.id=tr.id_ref_river_fk
    ) trash_properties
    LEFT JOIN bi.trash_river tr on tr.id=trash_properties.id
) t2
WHERE t2.id = t.id;

UPDATE bi.campaign_river c
SET feature_collection = json_build_object(
    'type', 'Feature', 'geometry', st_asgeojson(st_transform(ST_SetSRID(c2.the_geom, 2154), 4326)) :: json,
    'properties', c2.properties)
FROM (
    SELECT cr.id, cr.the_geom as the_geom,
        json_strip_nulls (row_to_json(campaign_properties)) as properties
    FROM (
        SELECT cr.id,
            c.id as campaign_id,
            trash.trashes_by_type,
            cr.distance,
            cr.trash_per_km,
            cr.trash_count,
            c.isaidriven,
            u.firstname,
            r.id as river_id,
            r.code as river_code,
            r.name as river_name
        FROM bi.campaign_river cr
            LEFT JOIN campaign.campaign c ON c.id=cr.id_ref_campaign_fk
            LEFT JOIN campaign.user u ON u.id=c.id_ref_user_fk
            LEFT JOIN referential.river r ON r.id=cr.id_ref_river_fk
            LEFT JOIN (
                SELECT id_ref_campaign_fk,
                    ARRAY_AGG(JSON_BUILD_OBJECT(COALESCE(name, 'no_type'), nb_trash)) trashes_by_type
                FROM(
                    SELECT tr.id_ref_campaign_fk, tt.name, count(tr.id) nb_trash
                    FROM bi.trash_river tr
                    LEFT JOIN bi.trash t on t.id=tr.id_ref_trash_fk
                    LEFT JOIN campaign.trash_type tt on tt.id=t.id_ref_trash_type_fk
                    GROUP BY tr.id_ref_campaign_fk, tt.name
                ) sub
                GROUP BY id_ref_campaign_fk
            ) trash ON trash.id_ref_campaign_fk = cr.id_ref_campaign_fk
    ) campaign_properties
    LEFT JOIN bi.campaign_river cr on cr.id=campaign_properties.id
) c2
WHERE c2.id = c.id;

