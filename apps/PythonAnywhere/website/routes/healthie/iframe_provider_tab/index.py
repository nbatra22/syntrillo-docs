# Path: ./apps/PythonAnywhere/website/routes/healthie/iframe_provider_tab/index.py

from flask import Blueprint, request, jsonify, render_template, abort
import json
import random
import os

# python.analysis.extraPaths added into .vscode/settings.json
from syntrillo.api_healthie.misc import extract_healthie_user_id_from_url
from syntrillo.api_healthie.user import HealthieUser
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.pseudonyms_management.temporary_lookup_codes_management import TemporaryLookUpCodesManagement
from syntrillo.system.iframe_validator import IframeValidator
from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets

# -------------------------------------------------
iframe_healthie_provider_tab_index_bp = Blueprint('iframe_healthie_provider_tab_index', __name__)

@iframe_healthie_provider_tab_index_bp.route('/iframe_healthie_provider_tab', methods=['GET'])
def iframe_healthie_provider_tab_index():
    """
    iframe displayed in :

    Provider portal, client Extra tab:
        hl_current_user_id: 1033222 # that's the provider ID
        referrer_url: https://securestaging.gethealthie.com/users/1035117  # that's the patient ID

    """

    # --------------------------------------------------------------------
    # Check if the request origin/referer is allowed
    iframe_validator = IframeValidator()
    iframe_valid, iframe_log = iframe_validator.is_request_allowed(request)
    if not iframe_valid:
        abort(403, description="Access Denied")

    # --------------------------------------------------------------------
    # load secrets and environment variables to retrieve local environment specific tweaks used mainly for debugging
    secrets = LocalEnvironmentAndSecrets(load_healthie_secrets=True)

    # --------------------------------------------------------------------
    # get healthie_provider_id and healthie_user_id from URL parameters

    # Retrieve the JSON data from the GET request
    data_get_request = request.args.to_dict()

    # Extract hl_current_user_id from data_get_request
    # here it is the provider id
    healthie_provider_id = data_get_request.get('hl_current_user_id')
    if healthie_provider_id is None:
        if os.getenv('OVERDIDE_HEALTHIE_PROVIDER_ID') is not None:
            healthie_provider_id = os.getenv('OVERDIDE_HEALTHIE_PROVIDER_ID')
        else:
            healthie_provider_id = "1033222" # "-1"

    healthie_user_id = extract_healthie_user_id_from_url(data_get_request.get('referrer_url'))

    if healthie_user_id is None: # if no patient_id in the referrer_url (eg local run), then we use a default one.
        if os.getenv('OVERDIDE_HEALTHIE_USER_ID') is not None:
            healthie_user_id = os.getenv('OVERDIDE_HEALTHIE_USER_ID')
        else:
            # healthie_user_id = '-1'
            # healthie_user_id = "1035117" # with onboarding forms
            # healthie_user_id = "1209727" # with syntrillo_internal_key
            # healthie_user_id = "1525423" # Patient AWS Test
            healthie_user_id = "2062692" # Patient AWS Test 5 (no BP data)
            # healthie_user_id = "2062877" # Patient AWS Test 6 (hypertensive)
            # healthie_user_id = "1562903" # Crispy Bacon
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
    # We do not pass healthie_user_id if the patient is registered at Syntrillo
    if syntrillo_internal_key is not None:
        healthie_user_id = "Not transmitted"

    # --------------------------------------------------------------------
    # milliseconds_delay used to delay the rendering of the iframe tabs

    # use a short delay by default
    milliseconds_delay_default = 100

    if secrets.is_lambda() and secrets.is_staging():
        # may require a longer delay on AWS Lambda staging
        milliseconds_delay_default = 500

    # if os env variable MILLISECONDS_DELAY exists use it else use default
    #   : useful locally since some delay needed to prevent a server error on VSCode Live Server
    milliseconds_delay = int( os.getenv('MILLISECONDS_DELAY', milliseconds_delay_default) )

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
            'healthie/iframe_provider_tab/demo/index.html',
        )

    elif is_test:
        # render the test template
        return render_template(
            'healthie/iframe_provider_tab/test/index.html',
        )

    else:

    # --------------------------------------------------------------------
    # render the template
        return render_template(
            # 'healthie/iframe_provider_tab/x-index.html',
            'healthie/iframe_provider_tab/index.html',
            healthie_provider_id=healthie_provider_id,
            patient_not_registered_at_syntrillo=patient_not_registered_at_syntrillo,
            healthie_user_id=healthie_user_id,
            temporary_lookup_code=temporary_lookup_code,
            milliseconds_delay=milliseconds_delay,
            iframe_log=iframe_log
        )
