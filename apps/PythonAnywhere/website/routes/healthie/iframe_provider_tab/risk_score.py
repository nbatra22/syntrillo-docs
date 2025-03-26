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

iframe_healthie_provider_tab_risk_score_bp = Blueprint('iframe_healthie_provider_tab_risk_score_bp', __name__)

from syntrillo.system.logger import logger


@iframe_healthie_provider_tab_risk_score_bp.route('/healthie/iframe_provider_tab/risk_score', methods=['GET','POST'])
def iframe_healthie_provider_tab_risk_score():
    """

    This endpoint is used to display blood pressure tab, which is called by the healthie_iframe_provider_tab index.html.

    Visualizes blood pressure analysis table and a pdf download button.

    To do:
        - Add form to html to allow provider options to:
            a. show/hide patient name
            b. custom name report

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
        'healthie/iframe_provider_tab/risk_score.html',
        healthie_provider_id=healthie_provider_id,
        healthie_user_id=healthie_user_id,
        temporary_lookup_code=temporary_lookup_code,
        patient_not_registered_at_syntrillo=(patient_not_registered_at_syntrillo_str == 'True')
    )
