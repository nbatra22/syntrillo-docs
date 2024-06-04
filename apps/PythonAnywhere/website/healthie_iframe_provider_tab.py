# Path: ./apps/PythonAnywhere/website/healthie_iframe_provider_tab.py

"""

route to healthie_iframe_provider_tab and related actions

"""

from flask import Blueprint, request, jsonify, render_template
import json

import os
import sys

# ----- healthie package integration --------------

# python anywhere requirements
#    pip install python-dotenv

# python.analysis.extraPaths added into .vscode/settings.json
from syntrillo.api_healthie.misc import extract_user_id_from_url
from syntrillo.patient_onboarding.manager import PatientOnboardingManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.patient_initialization.accounts_pairing import AccountsPairing


# -------------------------------------------------

healthie_iframe_provider_tab_bp = Blueprint('healthie_iframe_provider_tab', __name__)


# =============================================================================================================
# IFRAME PROVIDER TAB

# TODO : auto select the tab that is making the most sense with aria-selected="true"


@healthie_iframe_provider_tab_bp.route('/iframe_healthie_provider_tab', methods=['GET'])
def iframe_healthie_provider_tab():
    """
    iframe displayed in :

    Provider portal, client Extra tab:
        hl_current_user_id: 1033222 # that's the provider ID
        referrer_url: https://securestaging.gethealthie.com/users/1035117  # that's the patient ID

    """

    # --------------------------------------------------------------------
    # Retrieve the JSON data from the GET request
    data_get_request = request.args.to_dict()

    # Log the data to a local file
    with open('ignore_healthy_iframes_logs.txt', 'a') as f:
        f.write(json.dumps(data_get_request) + '\n\n')

    # Extract hl_current_user_id from data_get_request
    # here it is the provider id
    provider_id = data_get_request.get('hl_current_user_id')
    if provider_id is None:
        provider_id = "1033222" # "-1"

    patient_id = extract_user_id_from_url(data_get_request.get('referrer_url'))
    if patient_id is None: # if no patient_id in the referrer_url (eg local run), then we use a default one.
        # patient_id = '-1'
        patient_id = "1035117" # with onboarding forms
        # patient_id = "1209727" # with syntrillo_internal_key

    # --------------------------------------------------------------------
    # Load environment variables from .env file
    dotenv_path = ".env"

    # inits
    patient_status = []
    inconsistencies = []
    pseudonyms = None

    if patient_id != '-1' :
        if False: # False to speed things up
            # Fetch patient status using PatientOnboardingManager
            onboarding_manager = PatientOnboardingManager(dotenv_path=dotenv_path)
            patient_status = onboarding_manager.get_user_status(user_id=patient_id)
            inconsistencies = onboarding_manager.get_inconsistencies(user_id=patient_id)

        # fetch patient pseudonyms : syntrillo_user_id and pseudo_code_for_tenovi_phi_access
        lookup_manager = LookUpCodesManagement()
        pseudonyms = lookup_manager.retrieve_entry_by_healthy_user_id(patient_id)
        patient_not_registered_at_syntrillo = ( pseudonyms is None )


    # --------------------------------------------------------------------

    # TODO : get temporary_pseudo_code from the database for this patient_id with the 'iFrame' purpose

    # Render the 'healthie_provider_tab.html' template with the provided data
    return render_template('healthie_provider_tab.html',
                           data_get_request=data_get_request,
                           provider_id=provider_id,
                           patient_id=patient_id,
                           patient_status=patient_status,
                           inconsistencies=inconsistencies,
                           pseudonyms=pseudonyms, # TODO : not to be returned in production
                           patient_not_registered_at_syntrillo=patient_not_registered_at_syntrillo,
                           )


# =============================================================================================================
# BUTTONS IN PROVIDER TAB IFRAME

@healthie_iframe_provider_tab_bp.route('/healthie_onboarding_generate_personalized_form', methods=['POST'])
def healthie_onboarding_generate_personalized_form():
    """
    This endpoint generates a personalized Intake Form

    It is located in the Provider client screens - extra tab

    """

    # Retrieve the JSON data from the POST request
    data_post_request = request.form.to_dict()

    # Log the data to a local file
    with open('ignore_healthy_onboarding_logs.txt', 'a') as f:
        f.write(json.dumps(data_post_request) + '\n\n')

    patient_id = data_post_request.get('patient_id')
    provider_id = data_post_request.get('provider_id')
    send_request_to_patient = data_post_request.get('send_request_to_patient')

    # Convert send_request_to_patient to a boolean
    send_request_to_patient_bool = send_request_to_patient.lower() in ['on', 'true'] if send_request_to_patient else False

    # --------------------------------------------------------------------
    # Load environment variables from .env file
    dotenv_path = ".env"

    # new instance of onboarding_manager with the dotenv API key
    onboarding_manager = PatientOnboardingManager(dotenv_path=dotenv_path)

    new_form = onboarding_manager.build_personalized_intake_form(
        user_id=patient_id,
        send_completion_request=send_request_to_patient_bool
    )

    #  : log = generate_from(patient_id)
    log = 'log produced by function healthie_onboarding_generate_personalized_form'

    # return status
    log += f"\npatient_id {patient_id}"
    log += f"\nprovider_id {provider_id}"
    log += f"\nsend_request_to_patient {send_request_to_patient_bool}"
    log += f"\n\nnew_form\n " + json.dumps(new_form, indent=4)


    # return log as simple basic text, that will be displayed in a HTML textarea
    return jsonify({'log': log}), 200

@healthie_iframe_provider_tab_bp.route('/tenovi_generate_temporary_pairing_code_form', methods=['POST'])
def tenovi_generate_temporary_pairing_code_form():
    """
    This endpoint generates a pairing code to be entered in the Tenovi platform 'Patient ID' field by the study coordinator.

    """

    # Retrieve the JSON data from the POST request
    data_post_request = request.form.to_dict()

    # Log the data to a local file
    with open('ignore_healthy_onboarding_logs.txt', 'a') as f:
        f.write(json.dumps(data_post_request) + '\n\n')

    patient_id = data_post_request.get('patient_id')  # aka healthy_user_id
    provider_id = data_post_request.get('provider_id')

    # Get syntrillo_internal_key from patient_id
    lookup_manager = LookUpCodesManagement()
    patient_entry = lookup_manager.retrieve_entry_by_healthy_user_id(patient_id)
    syntrillo_internal_key = patient_entry['syntrillo_internal_key']

    # Call AccountsPairing.create_and_return_unique_temporary_pseudo_code
    accounts_pairing = AccountsPairing(syntrillo_internal_key)
    temporary_pseudo_code = accounts_pairing.create_and_return_unique_temporary_pseudo_code()

    # Prepare log information
    log = f"Temporary Pseudo Code generated: {temporary_pseudo_code}\n"
    log += f"patient_id: {patient_id}\n"
    log += f"provider_id: {provider_id}\n"

    return jsonify({'log': log, 'temporary_pseudo_code': temporary_pseudo_code}), 200

@healthie_iframe_provider_tab_bp.route('/tenovi_pair_devices_form', methods=['POST'])
def tenovi_pair_devices_form():
    """
    This endpoint generates a pairing code to be entered in the Tenovi platform 'Patient ID' field by the study coordinator.

    """

    # Retrieve the JSON data from the POST request
    data_post_request = request.form.to_dict()

    patient_id = data_post_request.get('patient_id')  # aka healthy_user_id
    provider_id = data_post_request.get('provider_id')

    # TODO: need to get syntrillo_internal_key from patient_id from LookUpCodesManagement.retrieve_entry_by_healthy_user_id

    # TODO: call AccountsPairing.pair_devices_using_temporary_pseudo_code

    # TODO: have to return some logs listing the devices paired
    return 'hello', 200

@healthie_iframe_provider_tab_bp.route('/register_patient_at_syntrillo_form', methods=['POST'])
def register_patient_at_syntrillo_form():
    """
    This endpoint registers a patient at Syntrillo, and generate his syntrillo_internal_key.
    """

    # Retrieve the JSON data from the POST request
    data_post_request = request.form.to_dict()

    patient_id = data_post_request.get('patient_id')  # aka healthy_user_id
    provider_id = data_post_request.get('provider_id')

    # add a new entry in user_look_up_codes
    lookup_code_management = LookUpCodesManagement()
    entry_log = lookup_code_management.create_entry(healthy_user_id=patient_id)

    if entry_log is not None:
        log = { 'log' : {
                    'message' : "Patient registered at Syntrillo - Reload the page to see the changes.",
                    'entry_log' : entry_log # TODO : remove in production
             } }
    else:
        log = { 'log' : { 'message' : "Error", 'entry_log' : entry_log } }

    return jsonify( log ), 200

