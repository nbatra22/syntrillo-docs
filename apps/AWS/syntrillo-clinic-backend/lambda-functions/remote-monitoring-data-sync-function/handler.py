# Path: ./apps/PythonAnywhere/scheduled_tasks/healthie/device_measurement_sync.py
import json
import sys
import os

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

    # print("Patients:", patients)

    for patient in patients['users']:
        print("\n---------\n", patient['id'])

        entry = lookup_codes.retrieve_entry_by_healthie_user_id(patient['id'])

        if entry: # and patient['id'] == "1051529":
            sync = RemoteMonitoringDataSync(entry['syntrillo_internal_key'])

            overall_log1 = sync.sync_tenovi_to_syntrillo()

            if not overall_log1['success']:
                print(json.dumps(overall_log1, indent=4))

            else:
                print("tenovi to syntrillo : number_of_records_inserted : ", overall_log1['number_of_records_inserted'] )
                overall_log2 = sync.sync_syntrillo_to_healthie()
                if not overall_log2['success']:
                    print(json.dumps(overall_log2, indent=4))

                else:
                    print("syntrillo to healthie : number_of_records_inserted : ", overall_log2['number_of_records_inserted'] )

    lookup_codes.close_connection()