from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app, abort

from .post_management import PostManager

from syntrillo.system.iframe_validator import IframeValidator
from syntrillo.stroke_risk_score_v2.calc_risk_score import calculate_risk_score
from syntrillo.stroke_risk_score_v2.srs_iframe_db import insert_srs_iframe_data
from syntrillo.study_outcomes.patient_study_outcomes import PatientStudyOutcomes
from syntrillo.api_healthie.medications import HealthieMedications
from syntrillo.remote_monitoring.syntrillo_medications_db_manager import SyntrilloMedicationsDatabaseQueries
from syntrillo.medications.models import MedicationRecord
from syntrillo.medications.utils import create_medication, update_medication, delete_medication, get_medication_info_by_keyword

iframe_healthie_provider_tab_medications_bp = Blueprint('iframe_healthie_provider_tab_medications_bp', __name__)

from syntrillo.system.logger import logger


@iframe_healthie_provider_tab_medications_bp.route('/healthie/iframe_provider_tab/medications', methods=['GET','POST'])
def iframe_healthie_provider_tab_medications():
    """

    This endpoint is used to display medications tab, which is called by the healthie_iframe_provider_tab index.html.

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
        'healthie/iframe_provider_tab/medications.html',
        healthie_provider_id=healthie_provider_id,
        healthie_user_id=healthie_user_id,
        temporary_lookup_code=temporary_lookup_code,
        patient_not_registered_at_syntrillo=(patient_not_registered_at_syntrillo_str == 'True')
    )

@iframe_healthie_provider_tab_medications_bp.route('/healthie/iframe_provider_tab/medications/active_medications', methods=['GET','POST'])
def iframe_healthie_provider_tab_active_medications():
    """
    Returns list of active medications for a patient.
    """

    try:
        healthie_user_id = request.form.get('healthie_user_id')

        post_manager = PostManager()
        post_manager.get_pseudonyms_from_tab_post(request)

        syntrillo_internal_key = post_manager.syntrillo_internal_key

        db_manager = SyntrilloMedicationsDatabaseQueries()
        medications_data, log = db_manager.get_medication_records_for_patient(syntrillo_internal_key)
        print(f"***** MEDICATIONS DATA *****: {medications_data}")
        if log['success']:
            return jsonify({
                'success': True,
                'data': medications_data
            })
        else:
            return jsonify({
                'success': False,
                'error': log['error']
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@iframe_healthie_provider_tab_medications_bp.route('/healthie/iframe_provider_tab/medications/keywords/<keyword>', methods=['GET','POST'])
def iframe_healthie_provider_tab_keywords(keyword):
    """
    Returns list of keywords for a patient.
    """
    try:
        keywords = get_medication_info_by_keyword(keyword=keyword)
        return jsonify({
            'success': True,
            'data': keywords
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@iframe_healthie_provider_tab_medications_bp.route('/healthie/iframe_provider_tab/medications/create_medication', methods=['GET','POST'])
def iframe_healthie_provider_tab_create_medication():
    """
    Creates a medication.
    """
    try:
        post_manager = PostManager()
        post_manager.get_pseudonyms_from_tab_post(request)

        syntrillo_internal_key = post_manager.syntrillo_internal_key

        medication_name = request.form.get('medication_name')
        dosage_option_id = request.form.get('dosage_option_id')
        mirrored = request.form.get('mirrored')
        is_active = True if request.form.get('is_active') == 'yes' else False
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        dosage_amount = request.form.get('dosage_amount')
        dosage_unit = request.form.get('dosage_unit')
        comment = request.form.get('comment')
        directions = request.form.get('directions')
        frequency = request.form.get('frequency')
        dosing_interval = request.form.get('dosing_interval')
        dosing_schedule_rule = request.form.get('dosing_schedule_rule')
        dose_count = request.form.get('dose_count')
        time_of_day = request.form.get('time_of_day')

        medication_record = MedicationRecord(
            syntrillo_internal_key=syntrillo_internal_key,
            medication_name=medication_name,
            is_active=is_active,
            start_date=start_date,
            end_date=end_date,
            dosage_amount=dosage_amount,
            dosage_unit=dosage_unit,
            comment=comment,
            directions=directions,
            frequency=frequency,
            dosing_interval=dosing_interval,
            dosing_schedule_rule=dosing_schedule_rule,
            dose_count=dose_count,
            time_of_day=time_of_day,
        )
        create_medication(medication_record)
        return jsonify({
            'success': True,
            'data': medication_record.model_dump()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@iframe_healthie_provider_tab_medications_bp.route('/healthie/iframe_provider_tab/medications/update_medication', methods=['GET','POST'])
def iframe_healthie_provider_tab_update_medication():
    """
    Updates a medication.
    """
    try:
        post_manager = PostManager()
        post_manager.get_pseudonyms_from_tab_post(request)

        syntrillo_internal_key = post_manager.syntrillo_internal_key

        medication_id = request.form.get('medication_id')
        dosage_option_id = request.form.get('dosage_option_id')
        mirrored = request.form.get('mirrored')
        medication_name = request.form.get('medication_name')
        # category = request.form.get('category')
        is_active = True if request.form.get('is_active') == 'yes' else False
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        dosage_amount = request.form.get('dosage_amount')
        dosage_unit = request.form.get('dosage_unit')
        comment = request.form.get('comment')
        directions = request.form.get('directions')
        frequency = request.form.get('frequency')
        dosing_interval = request.form.get('dosing_interval')
        dosing_schedule_rule = request.form.get('dosing_schedule_rule')
        dose_count = request.form.get('dose_count')
        time_of_day = request.form.get('time_of_day')

        medication_record = MedicationRecord(
            medication_id=medication_id,
            syntrillo_internal_key=syntrillo_internal_key,
            medication_name=medication_name,
            dosage_option_id=dosage_option_id,
            # medication_category=medication_category,
            is_active=is_active,
            start_date=start_date,
            end_date=end_date,
            dosage_amount=dosage_amount,
            dosage_unit=dosage_unit,
            comment=comment,
            directions=directions,
            frequency=frequency,
            dosing_interval=dosing_interval,
            dosing_schedule_rule=dosing_schedule_rule,
            dose_count=dose_count,
            time_of_day=time_of_day,
            mirrored=mirrored,
        )
        update_medication(medication_record)
        return jsonify({
            'success': True,
            'data': medication_record.model_dump()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@iframe_healthie_provider_tab_medications_bp.route('/healthie/iframe_provider_tab/medications/delete_medication', methods=['GET','POST'])
def iframe_healthie_provider_tab_delete_medication():
    """
    Deletes a medication.
    """
    try:
        post_manager = PostManager()
        post_manager.get_pseudonyms_from_tab_post(request)
        syntrillo_internal_key = post_manager.syntrillo_internal_key
        medication_id = request.form.get('medication_id')
        delete_medication(medication_id, syntrillo_internal_key)
        return jsonify({
            'success': True,
            'data': medication_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
