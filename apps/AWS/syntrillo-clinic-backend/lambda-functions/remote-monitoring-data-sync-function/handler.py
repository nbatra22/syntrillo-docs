# Path: ./apps/PythonAnywhere/scheduled_tasks/healthie/device_measurement_sync.py

from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.remote_monitoring.data_sync import RemoteMonitoringDataSync

from aws_lambda_powertools import Logger
logger = Logger()

# XRay is in comment because this lambda generates to much traces (should be improved)
# from aws_xray_sdk.core import patch_all, xray_recorder
# patch_all()

@logger.inject_lambda_context(log_event=True)
def handler(event, context):

    healthie_utils = HealthieUtils()
    lookup_codes = LookUpCodesManagement()

    patients = healthie_utils.list_patients()

    for patient in patients['users']:

        entry = lookup_codes.retrieve_entry_by_healthie_user_id(patient['id'])

        if entry:
            sync = RemoteMonitoringDataSync(entry['syntrillo_internal_key'])

            log = sync.sync_tenovi_to_syntrillo_to_healthie()

            if log('success'):
                logger.info(f"Successfully synced data for patient {patient['id']}")
            else:
                logger.error(f"Failed to sync data for patient {patient['id']}. Log: {log}")

        else:
            logger.error(f"Failed to sync data for patient {patient['id']}. No entry found in lookup")

    lookup_codes.close_connection()
