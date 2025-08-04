
from flask import Blueprint, render_template, request, jsonify, current_app, abort, Response, send_file
import pandas as pd
import json
import base64
import io
from datetime import datetime

from .post_management import PostManager
from syntrillo.remote_monitoring.data_reporting_combined import DataReportingCombination
from syntrillo.remote_monitoring.data_reporting_medication_adherence import DataReportingMedicationAdherence
from syntrillo.remote_monitoring.data_reporting_blood_pressure import DataReportingBloodPressure
from syntrillo.bp_analysis.bp_analysis import BloodPressureAnalysis
from syntrillo.remote_monitoring.data_reporting_heart_rate import DataReportingHeartRate
from syntrillo.remote_monitoring.data_reporting_steps import DataReportingSteps
from syntrillo.data_structures.healthie_dataset_handler import DataStructureHealthieDatasetHandler

from syntrillo.api_healthie.medications import HealthieMedications

from syntrillo.system.iframe_validator import IframeValidator

iframe_healthie_provider_tab_forms_bp = Blueprint(
    'iframe_healthie_provider_tab_forms_bp',
    __name__,
    url_prefix='/healthie/iframe_provider_tab/forms',
    template_folder='templates'
)

from syntrillo.system.logger import logger

@iframe_healthie_provider_tab_forms_bp.route('', methods=['GET','POST'])
def iframe_healthie_provider_tab_forms():
    """

    This endpoint is used to display the forms tab, which is called by the healthie_iframe_provider_tab index.html.

    Menu to create and view forms.

    To do:

    """
    # Check if the request origin/referer is allowed
    iframe_validator = IframeValidator()
    iframe_valid, iframe_log = iframe_validator.is_request_allowed(request)
    if not iframe_valid:
        abort(403, description="Access Denied")


    healthie_provider_id = request.form.get('healthie_provider_id')
    healthie_user_id = request.form.get('healthie_user_id')
    temporary_lookup_code = request.form.get('temporary_lookup_code')
    patient_not_registered_at_syntrillo_str = request.form.get('patient_not_registered_at_syntrillo')

    return render_template(
        'healthie/iframe_provider_tab/forms.html',
        healthie_provider_id=healthie_provider_id,
        healthie_user_id=healthie_user_id,
        temporary_lookup_code=temporary_lookup_code,
        patient_not_registered_at_syntrillo=(patient_not_registered_at_syntrillo_str == 'True')
    )

@iframe_healthie_provider_tab_forms_bp.route('/<form_name>', methods=['GET'])
def iframe_healthie_provider_tab_load_form(form_name):

    print("------ Requested form: ", form_name)

    # allowed_forms = ['medications_form']

    # if form_name not in allowed_forms:
    #     abort(404)

    try:
        return render_template(f'healthie/iframe_provider_tab/forms/{form_name}.html', title=form_name.replace('_', ' ').title())
    except:
        abort(404)
