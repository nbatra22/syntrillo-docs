# Path: ./apps/PythonAnywhere/website/healthie/iframe_provider_tab/system.py
from flask import Blueprint, render_template, request, jsonify

from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement

iframe_healthie_provider_tab_system_bp = Blueprint('iframe_healthie_provider_tab_system_bp', __name__)

@iframe_healthie_provider_tab_system_bp.route('/healthie/iframe_provider_tab/system', methods=['POST'])
def iframe_healthie_provider_tab_system():
    # Retrieve the form data from the POST request
    #   : these are passed from the healthie_iframe_provider_tab index.html
    #   : healthie_user_id, is None, unless in panic mode
    healthie_provider_id = request.form.get('healthie_provider_id')
    healthie_user_id = request.form.get('healthie_user_id')
    temporary_lookup_code = request.form.get('temporary_lookup_code')
    patient_not_registered_at_syntrillo_str = request.form.get('patient_not_registered_at_syntrillo')

    # Pass the retrieved variables to the template
    return render_template(
        'healthie/iframe_provider_tab/system.html',
        healthie_provider_id=healthie_provider_id,
        healthie_user_id=healthie_user_id,
        temporary_lookup_code=temporary_lookup_code,
        patient_not_registered_at_syntrillo=(patient_not_registered_at_syntrillo_str == 'True')
    )


@iframe_healthie_provider_tab_system_bp.route('/healthie/iframe_provider_tab/system/register_patient_at_syntrillo_form', methods=['POST'])
def register_patient_at_syntrillo_form():
    """
    This endpoint registers a patient at Syntrillo, and creates a new entry in the user_look_up_codes table.
    """

    # Retrieve the JSON data from the POST request
    data_post_request = request.form.to_dict()

    healthie_user_id = data_post_request.get('healthie_user_id')

    # add a new entry in user_look_up_codes
    lookup_code_management = LookUpCodesManagement()
    entry_log = lookup_code_management.create_entry(healthy_user_id=healthie_user_id)

    if entry_log is not None:
        log = { 'log' : {
                    'message' : "Patient succesfully registered at Syntrillo - The page will reload to see the changes.",
                    'success' : True,
                    'entry_log' : "hidden", # entry_log
             } }
    else:
        log = { 'log' : {
                    'message' : "Error",
                    'success' : False,
                    'entry_log' : entry_log
                    } }

    return jsonify( log ), 200
