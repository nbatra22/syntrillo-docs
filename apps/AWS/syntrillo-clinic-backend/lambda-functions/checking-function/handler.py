import requests

from syntrillo.patient_initialization.accounts_pairing import AccountsPairing
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.pseudonyms_management.temporary_lookup_codes_management import TemporaryLookUpCodesManagement

def call_example_dot_com_url():
    response = requests.get("https://www.example.com")
    print(response.text)

def register_patient_devices():

    healthie_user_id = "1035117"

    # -------------------------------------------------------------------------
    # /iframe_healthie_provider_tab
    # -------------------------------------------------------------------------   

    # --------------------------------------------------------------------
    # get syntrillo_internal_key from healthie_user_id
    look_up_codes_management = LookUpCodesManagement()
    entry = look_up_codes_management.retrieve_entry_by_healthie_user_id(healthie_user_id)
    if entry is not None:
        syntrillo_internal_key = entry['syntrillo_internal_key']
    else:
        # here, we will enter in a panic mode, allowing the 'system' tab to create a new patient
        syntrillo_internal_key = None

    patient_not_registered_at_syntrillo = ( syntrillo_internal_key is None )

    # --------------------------------------------------------------------
    # get temporary look up code for the syntrillo_internal_key
    temporary_lookup_codes_management = TemporaryLookUpCodesManagement()

    if syntrillo_internal_key is not None:
        temporary_lookup_code = temporary_lookup_codes_management.create_temporary_pseudo_code(
            syntrillo_internal_key=syntrillo_internal_key,
            purpose=TemporaryLookUpCodesManagement.PURPOSE_HEALTHIE_IFRAME
            )
    else:
        temporary_lookup_code = None

    # --------------------------------------------------------------------
    # We do not pass healthie_user_id if the patient is registered at Syntrillo
    if syntrillo_internal_key is not None:
        healthie_user_id = "Not transmitted"

    # -------------------------------------------------------------------------
    # /healthie/iframe_provider_tab/devices
    # -------------------------------------------------------------------------   

    paired_devices = AccountsPairing.get_paired_devices(syntrillo_internal_key=syntrillo_internal_key)

    # -------------------------------------------------------------------------
    # /healthie/iframe_provider_tab/devices/tenovi_generate_temporary_pairing_code_form
    # -------------------------------------------------------------------------  

    # Call AccountsPairing.create_and_return_unique_temporary_pseudo_code
    accounts_pairing = AccountsPairing(syntrillo_internal_key)
    temporary_tenovi_pseudo_code = accounts_pairing.create_and_return_unique_temporary_pseudo_code()

    # -------------------------------------------------------------------------
    # /healthie/iframe_provider_tab/devices/tenovi_pair_devices_form
    # -------------------------------------------------------------------------

    pairing = AccountsPairing(syntrillo_internal_key)
    log = pairing.pair_devices_using_temporary_pseudo_code()

def handler(event, context):
    print(event)

    resource_path = event['path']
    print(f"Resource path: {resource_path}")

    if resource_path == "/test_network_outside_connectivity":
        call_example_dot_com_url()
        return {
            'statusCode': 200,
            'body': 'Called example.com'
        }
    
    if resource_path == "/register_patient_devices":
        register_patient_devices()
        return {
            'statusCode': 200,
            'body': 'Temporary ID created'
        }

    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!'
    }