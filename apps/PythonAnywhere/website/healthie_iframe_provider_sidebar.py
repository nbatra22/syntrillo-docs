# ./Syntrillo_Clinic/apps/PythonAnywhere/website/healthie_iframe_provider_sidebar.py

"""

route to healthie_iframe_provider_sidebar and related actions

"""

from flask import Blueprint, request, jsonify, render_template
import json

import os
import sys

# ----- healthie package integration --------------

# python anywhere requirements
#    pip install python-dotenv

# python.analysis.extraPaths added into .vscode/settings.json
from syntrillo.healthie.utils import HealthieUtils
from syntrillo.healthie.misc import extract_user_id_from_url
from syntrillo.healthie.forms import HealthieForms

from syntrillo.data.structures.data_structure import DataStructure
from syntrillo.data.structures.storage_manager import StorageManager

# -------------------------------------------------

healthie_iframe_provider_sidebar_bp = Blueprint('healthie_iframe_provider_sidebar', __name__)


# =============================================================================================================
# IFRAMES PROVIDER SIDE BAR

@healthie_iframe_provider_sidebar_bp.route('/iframe_healthie_provider_sidebar', methods=['GET'])
def iframe_healthie_provider_sidebar():
    """
    iframe displayed in :

    Provider portal, extra sidebar item:
        hl_current_user_id: 1033222 # that's the provider ID
        referrer_url: https://securestaging.gethealthie.com/


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

    # --------------------------------------------------------------------
    # Load environment variables from .env file
    dotenv_path = ".env"

    # Create an instance of HealthieAPI with the provided API key and organization
    utils_api = HealthieUtils(dotenv_path=dotenv_path)

    # Example: Get organization details
    organization_details = utils_api.get_organization_details()

    # Initialize StorageManager to access available data structures
    manager = StorageManager()
    all_structures = manager.list_all_structures()

    # Render the 'healthie_provider_sidebar.html' template with the provided data
    return render_template('healthie_provider_sidebar.html',
                           organization_details=organization_details,
                           data_get_request=data_get_request,
                           provider_id=provider_id,
                           all_structures=all_structures,
                           )

# =============================================================================================================
# BUTTONS IN PROVIDER SIDE BAR IFRAME


@healthie_iframe_provider_sidebar_bp.route('/healthie_build_form_from_data_structure', methods=['POST'])
def healthie_build_form_from_data_structure():
    """
    This endpoint builds a form from a data structure

    It is called by a button on the Provider extra sidebar pane

    """

    # Retrieve the JSON data from the POST request
    data_post_request = request.form.to_dict()

    # Log the data to a local file
    with open('ignore_healthy_onboarding_logs.txt', 'a') as f:
        f.write(json.dumps(data_post_request) + '\n\n')

    provider_id = data_post_request.get('provider_id')
    structureName = data_post_request.get('structureName')

    # Generate form (TODO)
    #  : log = generate_from(patient_id)
    log = 'log produced by function healthie_build_form_from_data_structure'

    # return status
    log += f"\nprovider_id {provider_id}"
    log += f"\nstructureName {structureName}"

    # TODO : create a function from what's below

    # --------------------------------------------------------
    # initialize Healthie API

    # Load environment variables from .env file
    dotenv_path = ".env"

    forms_api = HealthieForms(dotenv_path=dotenv_path)

    # --------------------------------------------------------
    # Initialize StorageManager
    storage_manager = StorageManager()

    # Initialize DataStructure
    data_structure = DataStructure(storage_manager)

    # Load JSON data from StorageManager
    data_structure.load_from_storage(structureName)

    # Transform JSON data for Healthie API
    _ = data_structure.transform_for_healthie_api()

    modules = data_structure.healthie_custom_modules

    # Print transformed data (or perform further actions)
    print(json.dumps(modules, indent=4))

    # Call the create_form_wrapper function to create a new form with the specified modules
    form_name = data_structure.data['metadata'].get('name')
    external_id = data_structure.data['metadata'].get('internal_name')
    if data_structure.data['metadata'].get('type') == "Charting Notes (for providers)" :
        use_for_charting = True
    else:
        use_for_charting = False
    use_for_program = False

    # Assuming 'healthie_api' is an instance of your HealthieAPI class
    response = forms_api.create_form_wrapper(
        form_name=form_name,
        external_id=external_id,
        use_for_charting=use_for_charting,
        use_for_program=use_for_program,
        modules=modules,
    )

    # Print the response data containing the form and modules
    log += '\n'
    log += json.dumps(response, indent=4)

    # return log as simple basic text, that will be displayed in a HTML textarea
    return jsonify({'log': log}), 200