# Path: ./apps/PythonAnywhere/website/healthie/iframe_provider_tab/index.py

from flask import Blueprint, request, jsonify, render_template
import json
import random

# python.analysis.extraPaths added into .vscode/settings.json
from syntrillo.api_healthie.misc import extract_healthie_user_id_from_url
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.pseudonyms_management.temporary_lookup_codes_management import TemporaryLookUpCodesManagement

# -------------------------------------------------

iframe_healthie_provider_tab_index_bp = Blueprint('iframe_healthie_provider_tab_index', __name__)

@iframe_healthie_provider_tab_index_bp.route('/iframe_healthie_provider_tab_index', methods=['GET'])
def iframe_healthie_provider_tab_index():
    """
    iframe displayed in :

    Provider portal, client Extra tab:
        hl_current_user_id: 1033222 # that's the provider ID
        referrer_url: https://securestaging.gethealthie.com/users/1035117  # that's the patient ID

    """

    # --------------------------------------------------------------------
    # get healthie_provider_id and healthie_user_id from URL parameters

    # Retrieve the JSON data from the GET request
    data_get_request = request.args.to_dict()

    # Log the data to a local file
    with open('ignore_healthy_iframes_logs.txt', 'a') as f:
        f.write(json.dumps(data_get_request) + '\n\n')

    # Extract hl_current_user_id from data_get_request
    # here it is the provider id
    healthie_provider_id = data_get_request.get('hl_current_user_id')
    if healthie_provider_id is None:
        healthie_provider_id = "1033222" # "-1"

    healthie_user_id = extract_healthie_user_id_from_url(data_get_request.get('referrer_url'))

    if healthie_user_id is None: # if no patient_id in the referrer_url (eg local run), then we use a default one.
        # healthie_user_id = '-1'
        # healthie_user_id = "1035117" # with onboarding forms
        # healthie_user_id = "1209727" # with syntrillo_internal_key
        healthie_user_id = "dummy" + str(random.randint(100000, 999999)) # without syntrillo_internal_key
        # healthie_user_id = "dummy456456" # without syntrillo_internal_key

    # --------------------------------------------------------------------
    # get syntrillo_internal_key from healthie_user_id
    look_up_codes_management = LookUpCodesManagement()
    entry = look_up_codes_management.retrieve_entry_by_healthy_user_id(healthie_user_id)
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

    return render_template(
        'healthie/iframe_provider_tab/index.html',
        healthie_provider_id=healthie_provider_id,
        patient_not_registered_at_syntrillo=patient_not_registered_at_syntrillo,
        healthie_user_id=healthie_user_id,
        temporary_lookup_code=temporary_lookup_code
        )

