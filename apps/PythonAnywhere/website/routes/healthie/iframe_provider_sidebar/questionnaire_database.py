# Path: ./apps/PythonAnywhere/website/routes/healthie/iframe_provider_sidebar/questionnaire_database.py

from flask import Blueprint, render_template, request, jsonify, send_file, abort

import json
import os
import io

from werkzeug.utils import secure_filename

# python.analysis.extraPaths added into .vscode/settings.json
from syntrillo.data_structures.storage_manager_database import DatabaseStorageManagerDatabase
from syntrillo.data_structures.questionnaire_healthie_manager import DataStructureQuestionnaireHealthieManager
from syntrillo.data_structures.xlsx_questionnaire_handler import DataStructureXlsxQuestionnaireHandler

iframe_healthie_provider_sidebar_questionnaire_database_bp = Blueprint('iframe_healthie_provider_sidebar_questionnaire_database_bp', __name__)

# ========================= HTML PAGE ==========================

@iframe_healthie_provider_sidebar_questionnaire_database_bp.route('/healthie/iframe_provider_sidebar/questionnaire_database', methods=['POST'])
def iframe_healthie_provider_sidebar_questionnaire_database():
    """
    This endpoint is used to display the questionnaire page in the provider sidebar iframe.
    It is called by the healthie_iframe_provider_sidebar index.html
    """

    healthie_provider_id = request.form.get('healthie_provider_id')

    # --------------------------------------------------------------------

    logs = []

    # Initialize StorageManager to access available data structures
    manager = DatabaseStorageManagerDatabase()
    all_structures = manager.list_all_structures_with_metadata()

    # ---
    return render_template(
        'healthie/iframe_provider_sidebar/questionnaire_database.html',
        healthie_provider_id=healthie_provider_id,
        all_structures=all_structures,
        logs=json.dumps(logs, indent=4, default=str),
        )

# ========================= DOWNLOAD ENDPOINT ==========================

@iframe_healthie_provider_sidebar_questionnaire_database_bp.route('/download/questionnaire_from_database/<id>')
def download_questionnaire_from_database(id):
    """
    This endpoint is used to download a questionnaire file from the database.

    Args:
        id (int): The id of the questionnaire to download.

    """

    # get the file from the database
    manager = DatabaseStorageManagerDatabase()

    excel_bytes, full_name, log = manager.retrieve_excel_file_by_id(id)

    if excel_bytes is None or log['success'] is False:
        abort(404)

    else:
        # Wrap the bytes data in an io.BytesIO object
        excel_file = io.BytesIO(excel_bytes)

        return send_file(
            excel_file,
            as_attachment=True,
            download_name=full_name,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )


# ========================= ENDPOINTS ==========================

def _checkbox_to_bool(checkbox):
    if checkbox is None:
        return False
    else:
        return True

@iframe_healthie_provider_sidebar_questionnaire_database_bp.route('/healthie/iframe_provider_sidebar/questionnaire_database/healthie_build_form_from_data_structure', methods=['POST'])
def healthie_build_form_from_data_structure():
    """
    This endpoint builds a form from the selected data structure

    It is called by a button on the Provider extra sidebar pane

    """

    # Retrieve the JSON data from the POST request
    data_post_request = request.form.to_dict()

    # --------------------------------------------------------

    # this id is the id of the structure in the database
    # which has unique(platform, name, version)
    structure_id = data_post_request.get('structure_id')

    # Initialize the Healthie manager
    healthie_manager = DataStructureQuestionnaireHealthieManager()

    # create_healthie_form_from_structure
    log = healthie_manager.create_healthie_form_from_structure_id(structure_id)

    return jsonify( log ), 200

@iframe_healthie_provider_sidebar_questionnaire_database_bp.route('/healthie/iframe_provider_sidebar/questionnaire_database/healthie_upload_and_validate_form', methods=['POST'])
def healthie_upload_and_validate_form():

    # Retrieve the JSON data from the POST request
    data_post_request = request.form.to_dict()

    # --------------------------------------------------------

    overall_log = {
        'success': True,
        'message': '',
        'log1': None,
        'log2': None,
        'must_reload': False,
    }

    # get parameter
    build_charting_note = _checkbox_to_bool(data_post_request.get('build_charting_note'))
    allow_overwrite = _checkbox_to_bool(data_post_request.get('allow_overwrite'))

    # -------------------------------------------------
    # ------- do some verification first --------------

    # ---
    # Check if the post request has the file part
    if 'file' not in request.files:
        overall_log['success'] = False
        overall_log['message'] = 'No file part in the request'
        return jsonify(overall_log), 200

    # ---
    file = request.files['file']

    # ---
    # If the user does not select a file, the browser also submits an empty part without filename
    if file.filename == '':
        overall_log['success'] = False
        overall_log['message'] = 'No selected file'
        return jsonify(overall_log), 200

    # ---
    # Check if the file is an xlsx file
    if file and not file.filename.endswith('.xlsx'):
        overall_log['success'] = False
        overall_log['message'] = 'Invalid file format, only .xlsx files are allowed'
        return jsonify(overall_log), 200

    # -------------------------------------------------
    # ------- process the file ------------------------

    filename = secure_filename(file.filename)

    # Read the file contents as bytes
    file_bytes = file.read()

    # ---
    # initialize the structure handler
    xlxs_structure_handler = DataStructureXlsxQuestionnaireHandler()

    # ---
    # parse the xlsx file to JSON
    json_data, log1 = xlxs_structure_handler.parse_xlsx_to_json(xlsx_file=file_bytes, xlsx_filename=filename)

    overall_log['log1'] = log1

    if not log1['success']:
        overall_log['success'] = False
        overall_log['message'] = 'Error parsing the xlsx file'
        return jsonify(overall_log), 200

    overall_log['json_data'] = json_data

    # ---
    # Store the structure into the database
    log2 = xlxs_structure_handler.store_json_structure_in_database(delete_existing=allow_overwrite)

    overall_log['log2'] = log2

    if not log2['success']:
        overall_log['success'] = False
        overall_log['message'] = 'Error storing the structure in the database'
        return jsonify(overall_log), 200


    return jsonify( overall_log ), 200

