from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app, abort

from .post_management import PostManager

from syntrillo.system.iframe_validator import IframeValidator
from syntrillo.stroke_risk_score_v2.calc_risk_score import calculate_risk_score
from syntrillo.stroke_risk_score_v2.srs_iframe_db import insert_srs_iframe_data
from syntrillo.study_outcomes.patient_study_outcomes import PatientStudyOutcomes

iframe_healthie_provider_tab_study_outcomes_bp = Blueprint('iframe_healthie_provider_tab_study_outcomes_bp', __name__)

from syntrillo.system.logger import logger


@iframe_healthie_provider_tab_study_outcomes_bp.route('/healthie/iframe_provider_tab/study_outcomes', methods=['GET','POST'])
def iframe_healthie_provider_tab_study_outcomes():
    """

    This endpoint is used to display study outcomes tab, which is called by the healthie_iframe_provider_tab index.html.

    Visualizes risk score section breakdown and all metrics attributed, retrieved by route below.

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
        'healthie/iframe_provider_tab/study_outcomes.html',
        healthie_provider_id=healthie_provider_id,
        healthie_user_id=healthie_user_id,
        temporary_lookup_code=temporary_lookup_code,
        patient_not_registered_at_syntrillo=(patient_not_registered_at_syntrillo_str == 'True')
    )


@iframe_healthie_provider_tab_study_outcomes_bp.route('/healthie/iframe_provider_tab/study_outcomes/data', methods=['POST'])
def iframe_healthie_provider_tab_study_outcomes_data():
    """
    This endpoint is used to get the data for the study outcomes tab.
    """

    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    syntrillo_internal_key_patient = post_manager.syntrillo_internal_key
    healthie_user_id = post_manager.pseudonyms['healthie_user_id']

    study_outcomes = PatientStudyOutcomes(syntrillo_internal_key_patient, healthie_user_id)
    study_outcomes_data = study_outcomes.get_study_outcomes()

    if study_outcomes_data is None:
        return jsonify({
            "success": True,
            "message": "No data available",
            "study_outcomes_data": {}
        })

    return jsonify({
        "success": True,
        "message": "Study outcomes data received successfully",
        "study_outcomes_data": study_outcomes_data
    })
