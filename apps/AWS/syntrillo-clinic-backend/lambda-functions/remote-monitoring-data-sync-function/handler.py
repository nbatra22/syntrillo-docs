
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.remote_monitoring.data_sync import RemoteMonitoringDataSync

from syntrillo.system.logger import logger
from syntrillo.system.tracer import tracer

@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, context):

    healthie_utils = HealthieUtils()
    lookup_codes = LookUpCodesManagement()

    patients = healthie_utils.list_patients()

    logger.info(f"Found {len(patients['users'])} patients over {patients['usersCount']}")

    for patient in patients['users']:

        entry = lookup_codes.retrieve_entry_by_healthie_user_id(patient['id'])

        if entry:
            sync = RemoteMonitoringDataSync(entry['syntrillo_internal_key'])

            log = sync.sync_tenovi_to_syntrillo_to_healthie()

            if log.get('success', False):
                logger.info(f"Successfully synced data for patient {entry['syntrillo_internal_key']}")
            else:
                logger.error( { "error" : f"Failed to sync data for patient {entry['syntrillo_internal_key']}", "log": log } )

        else:
            logger.error(f"Failed to sync data for this patient. No entry found in lookup")

    lookup_codes.close_connection()
