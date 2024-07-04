# Path: ./apps/PythonAnywhere/website/routes/healthie/iframe_provider_sidebar/questionnaire.py
from flask import Blueprint, render_template, request, jsonify

import json

# python.analysis.extraPaths added into .vscode/settings.json
from syntrillo.data_structures.storage_manager import DataStructureStorageManager
from syntrillo.data_structures.questionnaire_healthie_manager import DataStructureQuestionnaireHealthieManager
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
    manager = DataStructureStorageManager()
    all_structures = manager.list_all_structures_with_metadata()

    return render_template(
        'healthie/iframe_provider_sidebar/questionnaire.html',
        healthie_provider_id=healthie_provider_id,
        all_structures=all_structures,
        )

# ========================= ENDPOINTS ==========================

@iframe_healthie_provider_sidebar_questionnaire_bp.route('/healthie/iframe_provider_sidebar/questionnaire/healthie_build_form_from_data_structure', methods=['POST'])
def healthie_build_form_from_data_structure():
    """
    This endpoint builds a form from the selected data structure

    It is called by a button on the Provider extra sidebar pane

    """

    # Retrieve the JSON data from the POST request
    data_post_request = request.form.to_dict()

    # --------------------------------------------------------

    structure_name = data_post_request.get('structure_name')

    # Initialize the Healthie manager
    healthie_manager = DataStructureQuestionnaireHealthieManager()

    # create_healthie_form_from_structure
    log = healthie_manager.create_healthie_form_from_structure(structure_name)

    return jsonify( log ), 200

