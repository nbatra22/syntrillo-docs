"""
This script is run on PythonAnywhere to sync data between Tenovi and Syntrillo, at regular intervals.
"""

import json
import sys
import os

# -------------------------------------------------
# Add the project directory to the sys.path

if os.path.exists('/home/syntrillo/_this_is_PythonAnywhere_'):

    # add the sources directory to the sys.path
    company_packages_home = '/home/syntrillo/Syntrillo_Clinic/sources/'
    if company_packages_home not in sys.path:
        sys.path = [company_packages_home] + sys.path

# -------------------------------------------------

from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.remote_monitoring.data_sync import RemoteMonitoringDataSync

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
