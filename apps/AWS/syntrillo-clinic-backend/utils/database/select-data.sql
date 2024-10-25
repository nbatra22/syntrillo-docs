SELECT healthie_user_id, HEX(syntrillo_internal_key) FROM syntrillo$PseudonymManagement.user_look_up_codes where healthie_user_id = 5383853;
SELECT healthie_user_id, HEX(syntrillo_internal_key) FROM syntrillo$PseudonymManagement.user_look_up_codes where healthie_user_id = 5311367;

SELECT healthie_user_id, HEX(syntrillo_internal_key) FROM syntrillo$PseudonymManagement.user_look_up_temporary_codes where healthie_user_id = 1525423;

SELECT  * from syntrillo$HealthInformation.tenovi_raw_measurements where HEX(tenovi_raw_measurements.syntrillo_internal_key) = '849B0F5648AC4A08B6F19519A3BC3D51' limit 10;

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
ORDER BY tenovi_raw_measurements.timestamp_local
limit 10;

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
        tenovi_raw_measurements.data_json,
        JSON_UNQUOTE(JSON_EXTRACT(tenovi_raw_measurements.data_json, '$.timezone_offset')) as timezone_offset
FROM syntrillo$PseudonymManagement.user_look_up_codes
     JOIN syntrillo$HealthInformation.tenovi_raw_measurements ON user_look_up_codes.syntrillo_internal_key = tenovi_raw_measurements.syntrillo_internal_key
WHERE  JSON_UNQUOTE(JSON_EXTRACT(tenovi_raw_measurements.data_json, '$.timezone_offset')) = '0'
ORDER BY tenovi_raw_measurements.timestamp_local
limit 10;

SELECT  user_look_up_codes.healthie_user_id, 
        HEX(user_look_up_temporary_codes.syntrillo_internal_key), 
        user_look_up_temporary_codes.temporary_pseudo_code, 
        user_look_up_temporary_codes.date 
FROM syntrillo$PseudonymManagement.user_look_up_temporary_codes
     JOIN syntrillo$PseudonymManagement.user_look_up_codes ON user_look_up_codes.syntrillo_internal_key = user_look_up_temporary_codes.syntrillo_internal_key
WHERE user_look_up_codes.healthie_user_id = 5383853
ORDER BY user_look_up_temporary_codes.date;


SELECT CONCAT(
    "INSERT INTO syntrillo$HealthInformation.tenovi_raw_measurements syntrillo_internal_key , device_name, metric_name, value_1, value_2, timestamp_local, data_json, date) VALUES (",
    QUOTE('0x849B0F5648AC4A08B6F19519A3BC3D51'), ', ',
    QUOTE(device_name), ', ',
    QUOTE(metric_name), ', ',
    QUOTE(value_1), ', ',
    QUOTE(value_2), ', ',
    QUOTE(timestamp_local), ', ',
    QUOTE(data_json), ', ',    
    QUOTE(date), ');'
)
FROM syntrillo$HealthInformation.tenovi_raw_measurements
WHERE HEX(tenovi_raw_measurements.syntrillo_internal_key) = '341441B854D34D0F92FA40D05A01EF9F';


INSERT INTO syntrillo$HealthInformation.tenovi_raw_measurements (syntrillo_internal_key , device_name, metric_name, value_1, value_2, timestamp_local, data_json, date) VALUES (UNHEX('849B0F5648AC4A08B6F19519A3BC3D51'), 'Tenovi BPM - L', 'pulse', '86.00', '0.00', '2024-10-16T00:10:00.000000-04:00', '{"metric": "pulse", "created": "2024-10-16T04:10:28.109806Z", "value_1": "86.00", "value_2": "0.00", "timestamp": "2024-10-16T04:10:00.000000Z", "patient_id": "5383853", "device_name": "Tenovi BPM - L", "sensor_code": "10", "filter_params": {"measurement_index": 587}, "hardware_uuid": "297056120BD7", "hwi_device_id": "e9c24a26-7d69-490f-9546-93c5a31486aa", "timezone_offset": -4, "estimated_timestamp": false}', '2024-10-17 00:08:21');