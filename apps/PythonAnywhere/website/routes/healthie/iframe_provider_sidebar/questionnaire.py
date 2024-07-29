# Path: ./apps/PythonAnywhere/website/routes/healthie/iframe_provider_sidebar/questionnaire.py

from flask import Blueprint, render_template, request, jsonify

import json
import os

from werkzeug.utils import secure_filename

# python.analysis.extraPaths added into .vscode/settings.json
from syntrillo.data_structures.storage_manager import DataStructureStorageManager
from syntrillo.data_structures.questionnaire_healthie_manager import DataStructureQuestionnaireHealthieManager
from syntrillo.api_healthie.forms import HealthieForms
from syntrillo.data_structures.xlsx_questionnaire_handler import DataStructureXlsxQuestionnaireHandler

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

    # ---
    # create a storage_symlink in the static/healthie/documents/storage folder to the storage path and use it in the template
    source_path = manager.get_storage_path()

    # static_path is the path to the documents folder in the static folder from this python script
    static_path = os.path.join(os.path.dirname(__file__), '../../../static/healthie/documents/')

    # if this path exists creates a symlink to the storage path
    if os.path.exists(static_path):
        symlink_destination_path = os.path.join(static_path, 'storage_symlink')
        # test if the symlink exists
        if not os.path.exists(symlink_destination_path):
            # src: This is the source file path for which the symbolic link will be created.
            # dst: This is the target file path where symbolic link will be created.
            os.symlink(dst=symlink_destination_path, src=source_path, target_is_directory=True)
        symlink_available = True
    else:
        symlink_available = False

    # ---
    return render_template(
        'healthie/iframe_provider_sidebar/questionnaire.html',
        healthie_provider_id=healthie_provider_id,
        all_structures=all_structures,
        symlink_available=symlink_available,
        )

# ========================= ENDPOINTS ==========================

def _checkbox_to_bool(checkbox):
    if checkbox is None:
        return False
    else:
        return True

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

@iframe_healthie_provider_sidebar_questionnaire_bp.route('/healthie/iframe_provider_sidebar/questionnaire/healthie_upload_and_validate_form', methods=['POST'])
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

    # ---
    # get the storage path
    storage_manager = DataStructureStorageManager()
    storage_file_path = storage_manager.get_storage_path()

    # ---
    # save the file
    filename = secure_filename(file.filename)
    file_path = os.path.join(storage_file_path, filename)

    # Check if file already exists and handle overwrite logic
    if os.path.exists(file_path) and not allow_overwrite:
        overall_log['success'] = False
        overall_log['message'] = 'File already exists and overwriting is not allowed'
        return jsonify(overall_log), 200

    # Save the file to the storage path. Can overwrite existing file.
    file.save(file_path)

    # ---
    # initialize the structure handler
    xlxs_structure_handler = DataStructureXlsxQuestionnaireHandler()

    # ---
    # Parse the xlsx file to JSON
    json_data, log1 = xlxs_structure_handler.parse_xlsx_to_json(file_path)
    overall_log['log1'] = log1

    if not log1['success']:
        overall_log['success'] = False
        # Delete the uploaded file
        os.remove(file_path)
        overall_log['message'] = "Failed to parse to JSON data. File deleted"
        return jsonify( overall_log ), 200

    # ---
    # Remove .xlsx extension from filename
    filename_without_ext = os.path.splitext(file_path)[0]

    # ---
    # Store JSON data
    log2 = xlxs_structure_handler.store_json_structure(json_data, structure_name=filename_without_ext)
    overall_log['log2'] = log2

    if not log2['success']:
        overall_log['success'] = False
        # Delete the uploaded file
        os.remove(file_path)
        overall_log['message'] = "Failed to store JSON data. File deleted"
        return jsonify( overall_log ), 200

    # ---
    # build the form if requested
    if build_charting_note:
        healthie_manager = DataStructureQuestionnaireHealthieManager()
        log3 = healthie_manager.create_healthie_form_from_structure(filename_without_ext)
        overall_log['log3'] = log3

        if not log3['success']:
            overall_log['success'] = False
            overall_log['message'] = "Failed to build the form"
            return jsonify( overall_log ), 200
        else:
            overall_log['message'] = "File uploaded, stored and form built successfully"
            # must reload the page
            overall_log['must_reload'] = True

    else:
        overall_log['message'] = "File uploaded and stored successfully"
        # must reload the page
        overall_log['must_reload'] = True

    return jsonify( overall_log ), 200

