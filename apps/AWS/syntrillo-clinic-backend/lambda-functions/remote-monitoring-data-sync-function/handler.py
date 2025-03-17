
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.remote_monitoring.data_sync import RemoteMonitoringDataSync

from syntrillo.system.logger import logger
from syntrillo.system.tracer import tracer

import uuid

# @tracer.capture_lambda_handler
# @logger.inject_lambda_context(log_event=True)
# def handler(event, context):

#     healthie_utils = HealthieUtils()
#     lookup_codes = LookUpCodesManagement()

#     patients = healthie_utils.list_patients()

#     logger.info(f"Found {len(patients['users'])} patients over {patients['usersCount']}")

#     for patient in patients['users']:

#         entry = lookup_codes.retrieve_entry_by_healthie_user_id(patient['id'])

#         if entry:
#             sync = RemoteMonitoringDataSync(entry['syntrillo_internal_key'])

#             log = sync.sync_tenovi_to_syntrillo_to_healthie()

#             if log.get('success', False):
#                 logger.info(f"Successfully synced data for patient {entry['syntrillo_internal_key']}")
#             else:
#                 logger.error( { "error" : f"Failed to sync data for patient {entry['syntrillo_internal_key']}", "log": log } )

#         else:
#             logger.error(f"Failed to sync data for this patient. No entry found in lookup")

#     lookup_codes.close_connection() 

@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    action = event.get('action')
    
    if action == 'list_patients':
        return list_patients()
    elif action == 'sync_patient':
        return sync_patient(event.get('id'))
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


