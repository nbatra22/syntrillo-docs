from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.remote_monitoring.data_sync import RemoteMonitoringDataSync

from syntrillo.system.logger import logger
from syntrillo.system.tracer import tracer

import uuid

@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    print(event)

    # Steps triggered by Tenovi webhooks:
    # 1. Extract patient_id and measurement data from event
    # 2. Push these measurements to MySQL database
    # 3. Validate systolic BP (value_1)
    # 4. Send notification to clinicians when extreme blood pressure (>170 || <90) is detected

    # Event format:
    # {
    #   "metric": "pulse",
    #   "device_name": "Tenovi BPM",
    #   "hwi_device_id": "12345678-abcd-1234-abcd-1234567890ab",
    #   "patient_id": "54321",
    #   "hardware_uuid": "1234ABCD5678",
    #   "sensor_code": "10",
    #   "value_1": "100.00",
    #   "value_2": "0.00",
    #   "created": "2025-01-16T17:34:47.025219Z",
    #   "timestamp": "2025-01-16T17:34:47.025219Z",
    #   "timezone_offset": 0,
    #   "estimated_timestamp": false,
    #   "filter_params": null
    # }

    # {
    #     "metric": "string",
    #     "device_name": "string",
    #     "hwi_device_id": "string",
    #     "patient_id": "string",
    #     "hardware_uuid": "string",
    #     "sensor_code": "string",
    #     "value_1": "string",
    #     "value_2": "string",
    #     "created": "2019-08-24T14:16:18Z",
    #     "timestamp": "2019-08-24T14:15:22Z",
    #     "timezone_offset": -2147483648,
    #     "estimated_timestamp": false,
    #     "filter_params": {}
    # } 

    # 1. Extract patient_id and measurement data from event
    patient_id = event.get('patient_id')
    systolic_bp = event.get('value_1')
    diastolic_bp = event.get('value_2')
    timestamp = event.get('timestamp')

    logger.info(f"Patient ID: {patient_id}")

    # 2. Push these measurements to MySQL database
    syntrillo_internal_key = get_syntrillo_internal_key_id_from_patient_id(patient_id) # <= we have to look for syntrillo_internal_key_id (syntrillo internal patient id)
    sync_patient(syntrillo_internal_key)

    # 3. Validate systolic BP (value_1)
    if systolic_bp is not None:
        if systolic_bp > 170 or systolic_bp < 90:
            # 4. Send notification to clinicians when extreme blood pressure (>170 || <90) is detected
            notify_clinicians()

    return {
        'statusCode': 200,
        'body': 'Hello World!'
    }

# Adds measurements to database (copy and pasyed from remote-monitoring-data-sync-function handler)
def sync_patient(patient_id):
    if not patient_id:
        raise ValueError("Patient ID is required")

    sync = RemoteMonitoringDataSync(uuid.UUID(patient_id))
    log = sync.sync_tenovi_to_syntrillo_to_healthie()

    if log.get('success', False):
        logger.info(f"Successfully synced data for patient {patient_id}")
        return {
            'success': True,
            'syntrillo_internal_key': patient_id,
            'error': None,
        }
    else:
        error_msg = f"Failed to sync data for patient {patient_id}"
        logger.error( { "error" : error_msg, "log": log } )
        return {
            'success': False,
            'error': error_msg,
            'syntrillo_internal_key': patient_id
        }

def notify_clinicians(patient_id):
    return 'Hello'

def get_syntrillo_internal_key_id_from_patient_id(event):
    return '4feec83c-b32a-4844-8ea2-f473f6f25da9'
