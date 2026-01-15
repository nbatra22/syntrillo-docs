# Path: ./apps/PythonAnywhere/website/routes/healthie/iframe_patient_sidebar/index.py
from flask import Blueprint, request, jsonify, render_template, abort
import json
import os

# python.analysis.extraPaths added into .vscode/settings.json
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.pseudonyms_management.temporary_lookup_codes_management import TemporaryLookUpCodesManagement
from syntrillo.system.iframe_validator import IframeValidator
from syntrillo.api_healthie.user import HealthieUser
from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets

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
    # Check if the request origin/referer is allowed
    iframe_validator = IframeValidator()
    iframe_valid, iframe_log = iframe_validator.is_request_allowed(request)
    if not iframe_valid:
        abort(403, description="Access Denied")

    # --------------------------------------------------------------------
    # Retrieve the JSON data from the GET request
    data_get_request = request.args.to_dict()

    # --------------------------------------------------------------------
    # Extract hl_current_user_id from data_get_request
    # here, it's the patient_id
    healthie_user_id = data_get_request.get('hl_current_user_id')

    if healthie_user_id is None: # if no patient_id in the referrer_url (eg local run), then we use a default one.
        if os.getenv('OVERDIDE_HEALTHIE_USER_ID') is not None:
            healthie_user_id = os.getenv('OVERDIDE_HEALTHIE_USER_ID')
        else:
            # healthie_user_id = '-1'
            # healthie_user_id = "1035117" # with onboarding forms
            # healthie_user_id = "1209727" # with syntrillo_internal_key
            healthie_user_id = "1966294" # Patient AWS Test 3
            # healthie_user_id = "1562903" # Crispy Bacon with syntrillo_internal_key: 99fddf03-9304-4e48-8711-0cc4d825eb94
            # healthie_user_id = "2315391" # Bob Barker
            # healthie_user_id = "dummy" + str(random.randint(100000, 999999)) # without syntrillo_internal_key
            # healthie_user_id = "dummy456456" # without syntrillo_internal_key
            # healthie_user_id = "1051529" # Omar's "Patient One" with devices

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
    # is it a demo or test mode?

    # get user tag
    if entry is not None and entry['healthie_user_id'] is not None:
        user = HealthieUser(entry['healthie_user_id'])
        is_demo = user.does_user_have_tag('demo')
        is_test = user.does_user_have_tag('test')
    else:
        is_demo = False
        is_test = False

    if is_demo:
        # render the demo template
        return render_template(
            'healthie/iframe_patient_sidebar/demo/index.html',
        )

    elif is_test:
        # render the test template
        return render_template(
            'healthie/iframe_patient_sidebar/test/index.html',
        )

    else:

        # --------------------------------------------------------------------
        # Flag for Don
        secrets = LocalEnvironmentAndSecrets(load_healthie_ids_secrets=True)
        healthie_patient_dashboard_ids = secrets.get_secret_value('healthie_ids', 'patient_dashboard_ids')

        if healthie_user_id in healthie_patient_dashboard_ids.split(','):
            healthie_user_id = "Not transmitted"
            return render_template(
                'healthie/iframe_patient_sidebar/index.html',
                patient_not_registered_at_syntrillo=patient_not_registered_at_syntrillo,
                healthie_user_id=healthie_user_id,
                temporary_lookup_code=temporary_lookup_code
            )
        else:
            healthie_user_id = "Not transmitted"
            return render_template(
                'healthie/iframe_patient_sidebar/coming_soon.html',
                healthie_user_id=healthie_user_id,
                temporary_lookup_code=temporary_lookup_code
            )
