import os
import base64
import uuid
import boto3
import json
from typing import List, Tuple
from datetime import datetime, date, timedelta
import pytz

from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger
from syntrillo.system.tracer import tracer
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets
from syntrillo.bp_alerts.bp_alert_manager import BloodPressureAlertManager

# TODO: comment these decorators when running locally
@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, context):

    action = event.get('action')

    if action == 'list_patients':
        return list_patients()
    elif action == 'run_analysis':
        syntrillo_internal_key = event.get('id')
        alert_manager = BloodPressureAlertManager(syntrillo_internal_key)
        return alert_manager.handle_2week_measurement()
    else:
        raise ValueError(f"Unknown action: {action}")


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
            patient_internal_key_list["users"].append({ "id": str(entry['syntrillo_internal_key'])})
            logger.info(f"Found patient {str(entry['syntrillo_internal_key'])} in lookup")
        else:
            error_msg = "Failed to find patient. No entry found in lookup"
            logger.error(error_msg)

    lookup_codes.close_connection()

    return patient_internal_key_list
