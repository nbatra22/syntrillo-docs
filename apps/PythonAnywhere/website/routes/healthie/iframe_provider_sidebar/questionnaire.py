from flask import Blueprint, render_template, request, jsonify

import json

# python.analysis.extraPaths added into .vscode/settings.json
from syntrillo.data_structures.data_structure import DataStructure
from syntrillo.data_structures.storage_manager import StorageManager
from syntrillo.api_healthie.forms import HealthieForms

iframe_healthie_provider_sidebar_questionnaire_bp = Blueprint('iframe_healthie_provider_sidebar_questionnaire_bp', __name__)

# ========================= HTML PAGE ==========================

@iframe_healthie_provider_sidebar_questionnaire_bp.route('/healthie/iframe_provider_sidebar/questionnaire', methods=['POST'])
def iframe_healthie_provider_sidebar_questionnaire():
    """
    This endpoint is used to display the questionnaire page in the provider sidebar iframe.
    It is called by the healthie_iframe_provider_sidebar index.html
    """

    healthie_provider_id = request.form.get('healthie_provider_id')

    # --------------------------------------------------------------------

    # Initialize StorageManager to access available data structures
    manager = StorageManager()
    all_structures = manager.list_all_structures()

    return render_template(
        'healthie/iframe_provider_sidebar/questionnaire.html',
        healthie_provider_id=healthie_provider_id,
        all_structures=all_structures,
        )

# ========================= ENDPOINTS ==========================

@iframe_healthie_provider_sidebar_questionnaire_bp.route('/healthie/iframe_provider_sidebar/questionnaire/healthie_build_form_from_data_structure', methods=['POST'])
def healthie_build_form_from_data_structure():
    """
    This endpoint builds a form from a data structure

    It is called by a button on the Provider extra sidebar pane

    """

    # Retrieve the JSON data from the POST request
    data_post_request = request.form.to_dict()

    healthie_provider_id = data_post_request.get('healthie_provider_id')
    structure_name = data_post_request.get('structure_name')

    # Generate form (TODO)
    #  : log = generate_from(patient_id)
    log = 'log produced by function healthie_build_form_from_data_structure'

    # return status
    log += f"\healthie_provider_id {healthie_provider_id}"
    log += f"\structure_name {structure_name}"

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
    data_structure.load_from_storage(structure_name)

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

    response = forms_api.create_form_wrapper(
        form_name=form_name,
        external_id=external_id,
        use_for_charting=use_for_charting,
        use_for_program=use_for_program,
        modules=modules,
    )

    if response is None:
        log = {
            "success": False,
            "message": "Error: Questionnaire form not created",
            "structure_name" : structure_name,
            'response': None
        }
    else:
        log = {
            "success": True,
            "message": "Questionnaire form created successfully",
            "structure_name" : structure_name,
            'response': response
        }

    return jsonify( log ), 200

