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
from syntrillo.api_healthie.constants import RHR_CATEGORY, WEIGHT_CATEGORY
from syntrillo.bp_analysis.bp_analysis import BloodPressureAnalysis
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.api_healthie.forms import HealthieForms
from syntrillo.system.iframe_validator import IframeValidator
from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.stroke_risk_score_v2.utils import get_biometric_data, calculate_bmi, get_patient_info
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.system.logger import logger
from syntrillo.stroke_risk_score_v2.agg_data import (
    get_srs_healthie_data,
    get_healthie_metric_data,
    calc_rhr_metadata,
    get_healthie_activity_and_inactivity_module_ids
)
from syntrillo.stroke_risk_score_v2.calc_risk_score import calculate_risk_score

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


@iframe_healthie_provider_tab_patient_dashboard_bp.route('/healthie/iframe_provider_tab/patient_view/blood_pressure', methods=['POST'])
def healthie_iframe_provider_tab_blood_pressure():
    """
    Retrieves summary stats data from BP Analysis class.
    """
    try:

        post_manager = PostManager()
        post_manager.get_pseudonyms_from_tab_post(request)

        if not post_manager.syntrillo_internal_key:
            return jsonify({
                'success': False,
                'error': 'No internal key found'
            })

        # Fetch blood pressure data
        bp_analysis = BloodPressureAnalysis(post_manager.syntrillo_internal_key)
        bp_data = bp_analysis.calculate_summary_stats()

        # Render the sidebar template with blood pressure data
        return jsonify({
            'success': True,
            'error': None,
            'data': bp_data
        })
    except Exception as e:
        logger.error(f"Error rendering blood pressure sidebar iframe: {e}")
        abort(500, description="An error occurred while processing your request.")


@iframe_healthie_provider_tab_patient_dashboard_bp.route('/healthie/iframe_provider_tab/patient_view/heart_rate', methods=['POST'])
def healthie_iframe_provider_tab_heart_rate():
    """
    Retrieves heart rate data from
    """
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)
    syntrillo_internal_key = post_manager.syntrillo_internal_key

    lookup_codes_manager = LookUpCodesManagement()
    entry = lookup_codes_manager.retrieve_entry_by_internal_key(syntrillo_internal_key)

    healthie_user_id = entry['healthie_user_id']

    # Get baseline (first 2 weeks), prior (2 weeks before current), and current (latest 2 weeks) RHR data
    healthie_utils = HealthieUtils()
    rhr_data = get_healthie_metric_data(healthie_utils, healthie_user_id, category=RHR_CATEGORY)
    rhr_metadata = calc_rhr_metadata(
        rhr_data=rhr_data,
        baseline_num_weeks=2,
        trailing_num_weeks=2,
        prior_num_weeks= 2
    ) if rhr_data else {}

    return jsonify({
        'average_rhr_baseline': rhr_metadata.get('average_rhr_baseline'),
        'average_rhr_trailing': rhr_metadata.get('average_rhr_trailing'),
        'average_rhr_prior': rhr_metadata.get('average_rhr_prior'),
        "baseline_start_date": rhr_metadata.get('baseline_start_date'),
        "baseline_end_date": rhr_metadata.get('baseline_end_date'),
        "prior_start_date": rhr_metadata.get('prior_start_date'),
        "prior_end_date": rhr_metadata.get('prior_end_date'),
        "current_start_date": rhr_metadata.get('current_start_date'),
        "current_end_date": rhr_metadata.get('current_end_date'),
    })


@iframe_healthie_provider_tab_patient_dashboard_bp.route('/healthie/iframe_provider_tab/patient_view/biometrics', methods=['POST'])
def healthie_iframe_provider_tab_biometrics():
    """
    This endpoint is used to retrieve biometrics data for a patient.

    NOTE: Currently this endpoint is only used for BMI, Sodium, and Physical Activity data but should be expanded to include all biometrics data
    when requested in a future feature.
    """

    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)
    syntrillo_internal_key = post_manager.syntrillo_internal_key
    lookup_codes_manager = LookUpCodesManagement()
    entry = lookup_codes_manager.retrieve_entry_by_internal_key(syntrillo_internal_key)
    healthie_user_id = entry['healthie_user_id']
    db_manager = SyntrilloDatabaseManager(syntrillo_internal_key)
    healthie_utils = HealthieUtils()

    # I believe that charting is no longer used for physical activity capture (9/8/25)
    # module_id_inactivity_charting = physical_activity_module_ids["module_id_inactivity_charting"]
    # module_id_activity_charting = physical_activity_module_ids["module_id_activity_charting"]

    physical_activity_module_ids = get_healthie_activity_and_inactivity_module_ids(db_manager=db_manager)
    module_id_inactivity_intake = physical_activity_module_ids["module_id_inactivity_intake"]
    module_id_activity_intake = physical_activity_module_ids["module_id_activity_intake"]

    inactivity_data = db_manager.get_all_patient_form_responses_by_module_id(module_id_inactivity_intake, syntrillo_internal_key)
    activity_data = db_manager.get_all_patient_form_responses_by_module_id(module_id_activity_intake, syntrillo_internal_key)

    inactivity_baseline, inactivity_prior, inactivity_current = None, None, None
    # Need minimum of 3 responses for baseline, prior, and current
    if inactivity_data and len(inactivity_data) >= 3:
        inactivity_baseline, inactivity_prior, inactivity_current = inactivity_data[-1], inactivity_data[1], inactivity_data[0]
    elif inactivity_data and len(inactivity_data) == 2:
        inactivity_baseline, inactivity_current = inactivity_data[-1], inactivity_data[0]
    elif inactivity_data and len(inactivity_data) == 1:
        inactivity_baseline = inactivity_data[0]
    else:
        logger.warning("Patient does not have at least 1 inactivity response...")


    activity_baseline, activity_prior, activity_current = None, None, None
    # Need minimum of 3 responses for baseline, prior, and current
    if activity_data and len(activity_data) >= 3:
        activity_baseline, activity_prior, activity_current = activity_data[-1], activity_data[1], activity_data[0]
    elif activity_data and len(activity_data) == 2:
        activity_baseline, activity_current = activity_data[-1], activity_data[0]
    elif activity_data and len(activity_data) == 1:
        activity_baseline = activity_data[0]
    else:
        logger.warning("Patient does not have at least 1 activity response...")

    physical_activity_data = {
        "inactive": {
            "inactivity_baseline": inactivity_baseline,
            "inactivity_prior": inactivity_prior,
            "inactivity_current": inactivity_current
        },
        "active": {
            "activity_baseline": activity_baseline,
            "activity_prior": activity_prior,
            "activity_current": activity_current
        }
    }

    # Get BMI data
    # 1.) get height (from patient info)
    patient_data = get_patient_info(healthie_user_id=healthie_user_id)
    height = patient_data.get("height", None)
    # 2.) get historical weight (from healthie metrics)
    weight_data_response = get_healthie_metric_data(healthie_utils, healthie_user_id, category=WEIGHT_CATEGORY)
    bmis = []
    for weight_data in weight_data_response:
        # 3.) calc bmi similar to PA
        bmis.append({
            'bmi': calculate_bmi(weight_data["metric_stat"], height),
            'date': weight_data["created_at"]
        })
        activity_baseline, activity_prior, activity_current = None, None, None

    # Need minimum of 3 responses for baseline, prior, and current
    # bmis are sorted in ascending order by date.
    bmi_baseline, bmi_prior, bmi_current = None, None, None
    if len(bmis) >= 3:
        bmi_baseline, bmi_prior, bmi_current = bmis[0], bmis[-2], bmis[-1]
    elif len(bmis) == 2:
        bmi_baseline, bmi_current = bmis[0], bmis[-1]
    elif len(bmis) == 1:
        bmi_baseline = bmis[0]
    else:
        logger.warning("Patient does not have at least 1 bmi available...")

    bmi_data = {
        "bmi_current": bmi_current,
        "bmi_prior": bmi_prior,
        "bmi_baseline": bmi_baseline
    }

    # Get Sodium Data
    secrets = LocalEnvironmentAndSecrets(load_healthie_secrets=True)
    if secrets.is_production():
        custom_module_form_id = "2455490"
    else:
        custom_module_form_id = "2203381"

    forms_manager = HealthieForms()
    autoscored_sections  = forms_manager.get_autoscored_sections(custom_module_form_id=custom_module_form_id,user_id=entry['healthie_user_id'])

    ssq_baseline, ssq_prior, ssq_current = None, None, None
    ssq_baseline_date, ssq_prior_date, ssq_current_date = None, None, None
    # Need minimum of 3 responses for baseline, prior, and current
    is_valid_autosections = autoscored_sections and len(autoscored_sections['formAnswerGroups']) > 0
    if is_valid_autosections:
        # SSQ responses are sorted in descending order (first=newest, last=oldest)
        ssq_responses = autoscored_sections['formAnswerGroups']
        if len(ssq_responses) >= 3:
            ssq_baseline = ssq_responses[-1]['autoscored_sections'][-1].get('value', None)
            ssq_baseline_date = ssq_responses[-1].get('created_at', None)
            ssq_prior = ssq_responses[1]['autoscored_sections'][-1].get('value', None)
            ssq_prior_date = ssq_responses[1].get('created_at', None)
            ssq_current = ssq_responses[0]['autoscored_sections'][-1].get('value', None)
            ssq_current_date = ssq_responses[0].get('created_at', None)
        elif len(ssq_responses) == 2:
            ssq_baseline = ssq_responses[-1]['autoscored_sections'][-1].get('value', None)
            ssq_baseline_date = ssq_responses[-1].get('created_at', None)
            ssq_current = ssq_responses[0]['autoscored_sections'][-1].get('value', None)
            ssq_current_date = ssq_responses[0].get('created_at', None)
        elif len(ssq_responses) == 1:
            ssq_baseline = ssq_responses[-1]['autoscored_sections'][-1].get('value', None)
            ssq_baseline_date = ssq_responses[-1].get('created_at', None)
        else:
            logger.warning("Patient does not have at least 1 activity response...")

    ssq_data = {
        "ssq_current": ssq_current,
        "ssq_prior": ssq_prior,
        "ssq_baseline": ssq_baseline,
        "ssq_baseline_date": ssq_baseline_date,
        "ssq_prior_date": ssq_prior_date,
        "ssq_current_date": ssq_current_date
    }


    return jsonify({
        "physical_activity_data":physical_activity_data,
        "bmi_data": bmi_data,
        "ssq_data": ssq_data
    })

@iframe_healthie_provider_tab_patient_dashboard_bp.route('/healthie/iframe_provider_tab/stroke_risk_factors', methods=['POST'])
def healthie_iframe_provider_tab_stroke_risk_factors():
    """
    This endpoint is used to retrieve stroke risk factor data for a patient.
    """

    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # Deal with patients not registered at Syntrillo
    if post_manager.patient_not_registered_at_syntrillo:
        return render_template('healthie/iframe_provider_tab/patient_not_registered.html')

    syntrillo_internal_key_patient = post_manager.syntrillo_internal_key

    try:

        risk_score, metrics, stroke_priority_score, independent_risk_variable_scores, dependent_risk_variable_contributions = calculate_risk_score(syntrillo_internal_key_patient)

        if risk_score is None and stroke_priority_score is None:
            return jsonify({
                'success': True,
                'message': 'No data available',
                'data': {
                    'risk_score': risk_score,
                    'metrics': metrics,
                    'priority_score': stroke_priority_score,
                    'independent_risk_variable_scores': independent_risk_variable_scores,
                    'dependent_risk_variable_contributions': dependent_risk_variable_contributions
                }
            })

        if metrics['srs_response_data'] is not None:
            metrics['srs_response_data'] = metrics['srs_response_data'][0].model_dump()

        # Return success response
        return jsonify({
            'success': True,
            'message': 'Charting note data received successfully',
            'data': {
                'risk_score': risk_score,
                'metrics': metrics,
                'priority_score': stroke_priority_score,
                'independent_risk_variable_scores': independent_risk_variable_scores,
                'dependent_risk_variable_contributions': dependent_risk_variable_contributions
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error retrieving risk score data: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500
