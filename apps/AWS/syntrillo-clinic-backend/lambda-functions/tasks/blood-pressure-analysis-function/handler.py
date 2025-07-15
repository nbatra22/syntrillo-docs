import json
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger
from syntrillo.system.tracer import tracer
from syntrillo.bp_alerts.bp_alert_manager import BloodPressureAlertManager

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
        syntrillo_internal_key = event.get('syntrillo_internal_key')
        healthie_user_id = event.get('healthie_user_id')

        # Input validation
        if syntrillo_internal_key is None or healthie_user_id is None:
            raise ValueError(f"No syntrillo_internal_key or healthie_user_id provided")

        logger.info(f"Building BloodPressureAlertManager for patient {syntrillo_internal_key}...")
        alert_manager = BloodPressureAlertManager(syntrillo_internal_key, healthie_user_id)

        if action == 'run_analysis':
            alert_manager.handle_two_week_measurement()
            alert_manager.handle_two_week_status()

            return {
                'statusCode': 200,
                'body': f'Successfully processed 2-week BP analysis event for patient {syntrillo_internal_key}.'
            }

        elif action == 'check_measurement_consistancy':
            alert_manager.handle_three_day_no_measurement()
            return {
                'statusCode': 200,
                'body': f'Successfully checked patient {syntrillo_internal_key}"s trailing 3 day BP measurement taking consistentcy.'
            }

        else:
            raise ValueError(f"Unknown action: {action}")

    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return {
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
                "healthie_user_id": patient["id"],
                "syntrillo_internal_key": str(entry['syntrillo_internal_key'])
            })
            logger.info(f"Found patient {str(entry['syntrillo_internal_key'])} in lookup")
        else:
            error_msg = "Failed to find patient. No entry found in lookup"
            logger.error(error_msg)

    lookup_codes.close_connection()

    return patient_internal_key_list
