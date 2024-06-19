# Path: ./apps/PythonAnywhere/website/routes/healthie/iframe_patient_sidebar/index.py
from flask import Blueprint, request, jsonify, render_template
import json

# python.analysis.extraPaths added into .vscode/settings.json
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.pseudonyms_management.temporary_lookup_codes_management import TemporaryLookUpCodesManagement


# -------------------------------------------------

iframe_healthie_patient_sidebar_bp = Blueprint('iframe_healthie_patient_sidebar_index', __name__)

@iframe_healthie_patient_sidebar_bp.route('/iframe_healthie_client_sidebar', methods=['GET'])
def iframe_healthie_patient_sidebar():
    """
    iframe displayed in :

    Patient portal, extra sidebar item:
        hl_current_user_id: 1035117 # that's the patient ID
        referrer_url: https://securestaging.gethealthie.com/

    """

    # --------------------------------------------------------------------
    # Retrieve the JSON data from the GET request
    data_get_request = request.args.to_dict()

    # Extract hl_current_user_id from data_get_request
    # here, it's the patient_id
    healthie_user_id = data_get_request.get('hl_current_user_id')

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

    # --------------------------------------------------------------------

    return render_template(
        'healthie/iframe_patient_sidebar/index.html',
        patient_not_registered_at_syntrillo=patient_not_registered_at_syntrillo,
        healthie_user_id=healthie_user_id,
        temporary_lookup_code=temporary_lookup_code
        )


