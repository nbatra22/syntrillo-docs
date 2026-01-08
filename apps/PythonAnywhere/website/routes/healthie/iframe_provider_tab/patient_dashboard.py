from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app, abort
from syntrillo.medications.helpers import sync_healthie_medications

from .post_management import PostManager

from syntrillo.system.iframe_validator import IframeValidator
from syntrillo.stroke_risk_score_v2.calc_risk_score import calculate_risk_score
from syntrillo.stroke_risk_score_v2.srs_iframe_db import insert_srs_iframe_data
from syntrillo.study_outcomes.patient_study_outcomes import PatientStudyOutcomes
from syntrillo.api_healthie.medications import HealthieMedications
from syntrillo.remote_monitoring.syntrillo_medications_db_manager import SyntrilloMedicationsDatabaseQueries
from syntrillo.medications.models import MedicationRecord, CommonMedication
from syntrillo.medications.utils import create_medication, update_medication, delete_medication, get_medication_info_by_keyword, get_common_medications_by_keyword, create_common_medication
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement

iframe_healthie_provider_tab_patient_dashboard_bp = Blueprint('iframe_healthie_provider_tab_patient_dashboard_bp', __name__)

from syntrillo.system.logger import logger


@iframe_healthie_provider_tab_patient_dashboard_bp.route('/healthie/iframe_provider_tab/patient_dashboard', methods=['GET','POST'])
def iframe_healthie_provider_tab_patient_dashboard():
    """
    Iframe for Healthie Provider Tab - Patient Dashboard
    """

    # --------------------------------------------------------------------
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
        'healthie/iframe_provider_tab/patient_dashboard/index.html',
        healthie_provider_id=healthie_provider_id,
        healthie_user_id=healthie_user_id,
        temporary_lookup_code=temporary_lookup_code,
        patient_not_registered_at_syntrillo=(patient_not_registered_at_syntrillo_str == 'True')
    )
