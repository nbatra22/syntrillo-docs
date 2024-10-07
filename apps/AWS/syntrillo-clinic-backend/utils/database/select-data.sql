SELECT healthie_user_id, HEX(syntrillo_internal_key) FROM user_look_up_codes where healthie_user_id = 5383853;

SELECT  * from syntrillo$HealthInformation.tenovi_raw_measurements limit 10;

SELECT user_look_up_codes.healthie_user_id, 
        HEX(user_look_up_codes.syntrillo_internal_key), 
        CONCAT(
        LOWER(SUBSTRING(HEX(user_look_up_codes.syntrillo_internal_key), 1, 8)), '-',
        LOWER(SUBSTRING(HEX(user_look_up_codes.syntrillo_internal_key), 9, 4)), '-',
        LOWER(SUBSTRING(HEX(user_look_up_codes.syntrillo_internal_key), 13, 4)), '-',
        LOWER(SUBSTRING(HEX(user_look_up_codes.syntrillo_internal_key), 17, 4)), '-',
        LOWER(SUBSTRING(HEX(user_look_up_codes.syntrillo_internal_key), 21))
        ) AS formatted_uuid_syntrillo_internal_key,
        HEX(user_look_up_codes.pseudo_code_for_tenovi_phi_access), 
        CONCAT(
        LOWER(SUBSTRING(HEX(user_look_up_codes.pseudo_code_for_tenovi_phi_access), 1, 8)), '-',
        LOWER(SUBSTRING(HEX(user_look_up_codes.pseudo_code_for_tenovi_phi_access), 9, 4)), '-',
        LOWER(SUBSTRING(HEX(user_look_up_codes.pseudo_code_for_tenovi_phi_access), 13, 4)), '-',
        LOWER(SUBSTRING(HEX(user_look_up_codes.pseudo_code_for_tenovi_phi_access), 17, 4)), '-',
        LOWER(SUBSTRING(HEX(user_look_up_codes.pseudo_code_for_tenovi_phi_access), 21))
        ) AS formatted_uuid_pseudo_code_for_tenovi_phi_access,       
        tenovi_raw_measurements.metric_name,
        tenovi_raw_measurements.timestamp_local,
        tenovi_raw_measurements.data_json
FROM syntrillo$PseudonymManagement.user_look_up_codes
     JOIN syntrillo$HealthInformation.tenovi_raw_measurements ON user_look_up_codes.syntrillo_internal_key = tenovi_raw_measurements.syntrillo_internal_key
WHERE user_look_up_codes.healthie_user_id = 5383853
ORDER BY tenovi_raw_measurements.timestamp_local;