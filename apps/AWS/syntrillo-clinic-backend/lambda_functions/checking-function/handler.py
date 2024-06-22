import requests

import pymysql
from syntrillo.databases_management.connection import DatabaseConnection

from syntrillo.patient_initialization.accounts_pairing import AccountsPairing
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.pseudonyms_management.temporary_lookup_codes_management import TemporaryLookUpCodesManagement

class Database:
    def __init__(self):
        db_conn = DatabaseConnection(DatabaseConnection.PSEUDONYM_DB)
        self.conn, self.tunnel = db_conn.create_connection(verbose=True)
        if not self.conn:
            raise ConnectionError("Failed to connect to the database.")
        self.cursor = self.conn.cursor()

    def delete_tables_content(self):
        self.cursor.execute("DELETE FROM logs")
        self.cursor.execute("DELETE FROM user_look_up_temporary_codes;")
        self.cursor.execute("DELETE FROM user_look_up_codes")
        self.conn.commit()

def call_example_dot_com_url():
    response = requests.get("https://www.example.com")
    return response

def register_patient_devices():

    healthie_user_id = "1035117"

    # create internal key
    look_up_codes_management = LookUpCodesManagement()
    look_up_codes_management.create_entry(healthie_user_id=healthie_user_id)
    entry = look_up_codes_management.retrieve_entry_by_healthie_user_id(healthie_user_id)
    syntrillo_internal_key = entry['syntrillo_internal_key']

    # create temp code
    temporary_lookup_codes_management = TemporaryLookUpCodesManagement()
    temporary_lookup_code = temporary_lookup_codes_management.create_temporary_pseudo_code(
        syntrillo_internal_key=syntrillo_internal_key,
        purpose=TemporaryLookUpCodesManagement.PURPOSE_HEALTHIE_IFRAME
    )

     # %%% ADDED TEST %%%
    print("syntrillo_internal_key :", syntrillo_internal_key)
    print("temporary_lookup_code :", temporary_lookup_code)
    # variables below will be reused for testing purposes
    syntrillo_internal_key_save = syntrillo_internal_key
    temporary_lookup_code_save = temporary_lookup_code
    # %%% ADDED TEST %%%
    
    # return render_template("healthie/iframe_provider_tab/index.html",
    #                         temporary_lookup_code=temporary_lookup_code,
    #                         iframe_healthie_provider_tab_devices_url = '/prod' + url_for("iframe_healthie_provider_tab_devices_bp.iframe_healthie_provider_tab_devices")
    #                        )

    # At this tage, patient is already created in the database 
    # with healthie_user_id & pseudo_code_for_tenovi

    # -------------------------------------------------------------------------
    # /iframe_healthie_provider_tab
    # -------------------------------------------------------------------------   

    # --------------------------------------------------------------------
    # get healthie_provider_id and healthie_user_id from URL parameters

    # # Retrieve the JSON data from the GET request
    # data_get_request = request.args.to_dict()

    # # Extract hl_current_user_id from data_get_request
    # # here it is the provider id
    # healthie_provider_id = data_get_request.get('hl_current_user_id')
    # if healthie_provider_id is None:
    #     healthie_provider_id = "1033222" # "-1"

    # healthie_user_id = extract_healthie_user_id_from_url(data_get_request.get('referrer_url'))

    # if healthie_user_id is None: # if no patient_id in the referrer_url (eg local run), then we use a default one.
    #     # healthie_user_id = '-1'
    #     healthie_user_id = "1035117" # with onboarding forms
    #     # healthie_user_id = "1209727" # with syntrillo_internal_key
    #     # healthie_user_id = "dummy" + str(random.randint(100000, 999999)) # without syntrillo_internal_key
    #     # healthie_user_id = "dummy456456" # without syntrillo_internal_key
    
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

     # %%% ADDED TEST %%%
    assert syntrillo_internal_key == syntrillo_internal_key_save
    # %%% ADDED TEST %%%

    # # --------------------------------------------------------------------
    # # We do not pass healthie_user_id if the patient is registered at Syntrillo
    # if syntrillo_internal_key is not None:
    #     healthie_user_id = "Not transmitted"

    # return render_template(
    #     'healthie/iframe_provider_tab/index.html',
    #     healthie_provider_id=healthie_provider_id,
    #     patient_not_registered_at_syntrillo=patient_not_registered_at_syntrillo,
    #     healthie_user_id=healthie_user_id,
    #     temporary_lookup_code=temporary_lookup_code
    #     )

    # -------------------------------------------------------------------------
    # /healthie/iframe_provider_tab/devices
    # -------------------------------------------------------------------------   

    # # get all pseudonyms from post temporary identifier
    # post_manager = PostManager()
    # post_manager.get_pseudonyms_from_index_post(request)

    # # deal with patients not registered at Syntrillo
    # if post_manager.patient_not_registered_at_syntrillo:
    #     return render_template('healthie/iframe_provider_tab/patient_not_registered.html')

    # --------------------------------------------------------------------
    # get paired devices from Tenovi API
    paired_devices = AccountsPairing.get_paired_devices(syntrillo_internal_key=syntrillo_internal_key)

    # %%% ADDED TEST %%%    
    print("paired_devices:", paired_devices)
    assert paired_devices == ['']
    # %%% ADDED TEST %%%

    # return render_template('healthie/iframe_provider_tab/devices.html',
    #                        temporary_lookup_code=post_manager.temporary_lookup_code,
    #                        healthie_provider_id=post_manager.healthie_provider_id,
    #                        paired_devices=paired_devices
    # )

    # -------------------------------------------------------------------------
    # /healthie/iframe_provider_tab/devices/tenovi_generate_temporary_pairing_code_form
    # -------------------------------------------------------------------------  

    # # get all pseudonyms from post temporary identifier
    # post_manager = PostManager()
    # post_manager.get_pseudonyms_from_tab_post(request)

    # Call AccountsPairing.create_and_return_unique_temporary_pseudo_code
    accounts_pairing = AccountsPairing(syntrillo_internal_key)
    temporary_tenovi_pseudo_code = accounts_pairing.create_and_return_unique_temporary_pseudo_code()

    # %%% ADDED TEST %%%
    assert temporary_tenovi_pseudo_code != None
    # %%% ADDED TEST %%%

    # if temporary_tenovi_pseudo_code is None:
    #     log = {
    #         "success": False,
    #         "message": "Error: Temporary Pseudo Code for Tenovi pairing not generated",
    #         'temporary_tenovi_pseudo_code': None
    #     }
    # else:
    #     log = {
    #         "success": True,
    #         "message": "Temporary Pseudo Code for Tenovi pairing generated successfully",
    #         'temporary_tenovi_pseudo_code': temporary_tenovi_pseudo_code
    #     }

    # return jsonify( log ), 200

    # -------------------------------------------------------------------------
    # /healthie/iframe_provider_tab/devices/tenovi_pair_devices_form
    # -------------------------------------------------------------------------

    # # get all pseudonyms from post temporary identifier
    # post_manager = PostManager()
    # post_manager.get_pseudonyms_from_tab_post(request)

    pairing = AccountsPairing(syntrillo_internal_key)
    log = pairing.pair_devices_using_temporary_pseudo_code()

    # %%% ADDED TEST %%%
    paired_devices = AccountsPairing.get_paired_devices(syntrillo_internal_key=syntrillo_internal_key)
    assert paired_devices == ['']
    # %%% ADDED TEST %%%

    # return jsonify( log ), 200

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
        Database().delete_tables_content()
        register_patient_devices()
        return {
            'statusCode': 200,
            'body': 'Patient  devices are registered'
        }

    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!'
    }