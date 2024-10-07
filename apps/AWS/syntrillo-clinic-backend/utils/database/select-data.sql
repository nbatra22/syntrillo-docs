SELECT healthie_user_id, HEX(syntrillo_internal_key) FROM user_look_up_codes where healthie_user_id = 5383853;

SELECT  * from tenovi_raw_measurements limit 10;

SELECT user_look_up_codes.healthie_user_id, HEX(user_look_up_codes.syntrillo_internal_key), tenovi_raw_measurements.metric_name
FROM syntrillo$PseudonymManagement.user_look_up_codes
     JOIN syntrillo$HealthInformation.tenovi_raw_measurements ON user_look_up_codes.syntrillo_internal_key = tenovi_raw_measurements.syntrillo_internal_key
WHERE user_look_up_codes.healthie_user_id = 5391367;