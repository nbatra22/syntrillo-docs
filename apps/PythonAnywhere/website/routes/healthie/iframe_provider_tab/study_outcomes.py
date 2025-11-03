from datetime import datetime
import uuid
from flask import Blueprint, render_template, request, jsonify, current_app, abort

from .post_management import PostManager

from syntrillo.system.iframe_validator import IframeValidator
from syntrillo.stroke_risk_score_v2.calc_risk_score import calculate_risk_score
from syntrillo.stroke_risk_score_v2.srs_iframe_db import insert_srs_iframe_data
from syntrillo.study_outcomes.patient_study_outcomes import PatientStudyOutcomes
from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets
from syntrillo.api_healthie.user import HealthieUser
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.stroke_risk_score_v2.agg_data import get_healthie_activity_data

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

    local_environment_and_secrets = LocalEnvironmentAndSecrets()
    is_production = local_environment_and_secrets.is_production()

    study_outcomes = PatientStudyOutcomes(syntrillo_internal_key_patient, healthie_user_id)
    primary_prevention_study_groups = study_outcomes.primary_prevention_study_group
    secondary_prevention_study_groups = study_outcomes.secondary_prevention_study_group

    healthie_user_manager = HealthieUser(healthie_user_id)
    user_group = healthie_user_manager.get_user_group_by_healthie_user_id()
    user_group_name = user_group['name'] if user_group else None
    user_group_id = user_group['id'] if user_group else None

    db_manager = SyntrilloDatabaseManager(syntrillo_internal_key_patient)
    activity_data = get_healthie_activity_data(db_manager, syntrillo_internal_key_patient)

    data = {
        'primary_prevention': None,
        'secondary_prevention': None,
        'user_group_name': user_group_name,
        'activity_data': activity_data,
    }

    if is_production:
        data['primary_prevention'] = study_outcomes.get_primary_prevention_data() if user_group_id in primary_prevention_study_groups else None
        data['secondary_prevention'] = study_outcomes.get_secondary_prevention_data() if user_group_id in secondary_prevention_study_groups else None
    else:
        data['primary_prevention'] = study_outcomes.get_primary_prevention_data()
        data['secondary_prevention'] = study_outcomes.get_secondary_prevention_data()

    return jsonify(data)
