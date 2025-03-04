
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.remote_monitoring.data_sync import RemoteMonitoringDataSync

from syntrillo.system.logger import logger
from syntrillo.system.tracer import tracer

import uuid
import os

import boto3
s3 = boto3.client('s3')

@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    patient_piis_json = list_patient_piis()
    csv_file = build_csv_file(patient_piis_json)
    s3.put_object(Bucket=os.getenv('PII_DATA_BUCKET'), Key='patient_piis/patient_piis.csv', Body=csv_file)

def build_csv_file(patient_piis):
    csv_file = ""
    for patient in patient_piis["users"]:
        csv_file += f"{patient['id']},{patient['name']}\n"
    return csv_file

def list_patient_piis():
    healthie_utils = HealthieUtils()
    patients = healthie_utils.list_patients()
    
    logger.info(f"Found {len(patients['users'])} patients over {patients['usersCount']}")

    # list all patients syntrillo_internal_key
    lookup_codes = LookUpCodesManagement()

    patient_internal_key_list = {"users": []}
    for patient in patients['users']:
        entry = lookup_codes.retrieve_entry_by_healthie_user_id(patient["id"])
        if entry:
            patient_internal_key_list["users"].append({ "id": str(entry['syntrillo_internal_key']), "name": patient["name"]})
            logger.info(f"Found patient {str(entry['syntrillo_internal_key'])} in lookup")
        else:
            error_msg = "Failed to find patient. No entry found in lookup"
            logger.error(error_msg)

    lookup_codes.close_connection()

    return patient_internal_key_list