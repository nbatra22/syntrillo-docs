import json
import uuid
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger
from syntrillo.system.tracer import tracer
from syntrillo.bp_alerts.bp_alert_manager import BloodPressureAlertManager
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager

# TODO: comment these decorators when running locally
@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    try:
        action = event.get('action', None)
        if not action:
            raise ValueError(f"No action provided")
        logger.info(f"Processing action: {action}")

        if action == 'list_patients':
            return list_patients()

        # BP Alert handling. In future, make this logic conditional for other functionality grouping
        syntrillo_internal_key = event.get('id')

        lookup_codes = LookUpCodesManagement()

        entry = lookup_codes.retrieve_entry_by_internal_key(syntrillo_internal_key=uuid.UUID(syntrillo_internal_key))
        healthie_user_id = entry['healthie_user_id']

        # Input validation
        if syntrillo_internal_key is None or healthie_user_id is None:
            raise ValueError(f"No syntrillo_internal_key or healthie_user_id provided")

        # Existing measurement validation
        db_manager = SyntrilloDatabaseManager(syntrillo_internal_key)
        record, log = db_manager.get_first_tenovi_device_data(device_name='Tenovi BPM - L')
        if log['success'] == False:
            return {
                'success': False,
                'error': log['error'],
                'statusCode': 500,
                'body': json.dumps({'error': log['error']})
            }

        if record is None:
            return {
                'success': False,
                'error': f"No recent measurement found for patient {syntrillo_internal_key}",
                'statusCode': 500,
                'body': json.dumps({'error': f"No recent measurement found for patient {syntrillo_internal_key}"})
            }

        # Initialize BloodPressureAlertManager
        logger.info(f"Building BloodPressureAlertManager for patient {syntrillo_internal_key}...")
        alert_manager = BloodPressureAlertManager(syntrillo_internal_key, healthie_user_id, calculate_timeframed_data=True)

        # Analyze patient blood pressure
        if action == 'analyze_patient_blood_pressure':

            has_recent_measurement = alert_manager.handle_five_day_measurement_check()

            if has_recent_measurement:
                return alert_manager.handle_two_week_alerts()
            else:
                return {
                    'success': True,
                    'error': None,
                    'statusCode': 200,
                    'body': f"2-week BP analysis was not run for patient {syntrillo_internal_key} because the patient has not recorded a measurement in the past 5 days."
                }

        else:
            return {
                'success': False,
                'error': f"Unknown action: {action}",
                'statusCode': 500,
                'body': json.dumps({'error': f"Unknown action: {action}"})
            }

    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return {
            'success': False,
            'error': f'An internal server error occurred: {e}',
            'statusCode': 500,
            'body': json.dumps({'error': f'An internal server error occurred: {e}'})
        }


def list_patients():
    healthie_utils = HealthieUtils()
    patients = healthie_utils.list_patients()

    logger.info(f"Found {len(patients['users'])} patients over {patients['usersCount']}")

    # list all patients syntrillo_internal_key
    lookup_codes = LookUpCodesManagement()

    patient_internal_key_list = {"users": []}
    for patient in patients['users']:
        entry = lookup_codes.retrieve_entry_by_healthie_user_id(patient["id"])
        if entry:
            patient_internal_key_list["users"].append({
                "id": str(entry['syntrillo_internal_key'])
            })
            logger.info(f"Found patient {str(entry['syntrillo_internal_key'])} in lookup")
        else:
            error_msg = "Failed to find patient. No entry found in lookup"
            logger.error(error_msg)

    lookup_codes.close_connection()

    return patient_internal_key_list
