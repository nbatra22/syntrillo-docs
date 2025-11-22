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
        post_manager = PostManager()
        post_manager.get_pseudonyms_from_tab_post(request)

        syntrillo_internal_key = post_manager.syntrillo_internal_key

        lookup_codes_manager = LookUpCodesManagement()
        entry = lookup_codes_manager.retrieve_entry_by_internal_key(syntrillo_internal_key)

        if entry is None:
            raise Exception(f"No pseudonym entry found for internal key: {syntrillo_internal_key}")

        healthie_user_id = entry.get('healthie_user_id')

        db_manager = SyntrilloMedicationsDatabaseQueries()
        medications_data, log = db_manager.get_patient_medications(syntrillo_internal_key)
        syntrillo_medication_ids = set(medications_data.keys())

        healthie_manager = HealthieMedications()
        response, log_healthie = healthie_manager.list_user_medications(healthie_user_id, active=True)
        healthie_medications = response.get('medications', []) if log_healthie['success'] else []
        logger.info(f"Fetched {len(healthie_medications)} active medications from Healthie for user {healthie_user_id}")

        if len(healthie_medications) > 0:
            sync_log = sync_healthie_medications(
                syntrillo_internal_key=syntrillo_internal_key,
                healthie_medications=healthie_medications,
                syntrillo_medication_ids=syntrillo_medication_ids
            )

            logger.info(f"Synced medications log: {sync_log}")

            if sync_log['medications_added'] > 0:
                # Refresh medications data after sync
                refreshed_db_manager = SyntrilloMedicationsDatabaseQueries()
                medications_data, log = refreshed_db_manager.get_patient_medications(syntrillo_internal_key)


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

@iframe_healthie_provider_tab_medications_bp.route('/healthie/iframe_provider_tab/medications/healthie_keywords/<keyword>', methods=['GET','POST'])
def iframe_healthie_provider_tab_healthie_medication_keywords(keyword=''):
    """
    Returns list of keywords for a patient.
    """
    try:
        if keyword:
            keywords = get_medication_info_by_keyword(keyword=keyword)
            keyword_dict = {}
            if keywords is not None and len(keywords) > 0:
                for keyword in keywords:
                    keyword_dict[keyword['id']] = {
                        'name': keyword['name'],
                        'dosage_options': keyword['dosage_options']
                    }
        else:
            keyword_dict = {}
        return jsonify({
            'success': True,
            'data': keyword_dict
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@iframe_healthie_provider_tab_medications_bp.route('/healthie/iframe_provider_tab/medications/syntrillo_keywords/<keyword>', methods=['GET','POST'])
def iframe_healthie_provider_tab_syntrillo_medication_keywords(keyword=''):
    """
    Returns list of keywords for a patient.
    """
    try:
        if keyword:
            similar_meds = get_common_medications_by_keyword(keyword=keyword)
            keyword_dict = {}
            if similar_meds is not None and len(similar_meds) > 0:
                for medication in similar_meds:
                    keyword_dict[medication['id']] = {
                        'name': medication['common_name'],
                        'category': medication['category'],
                        'supercategory': medication['supercategory'],
                        'category_custom': medication['category_custom'],
                        'supercategory_custom': medication['supercategory_custom'],
                    }
        else:
            keyword_dict = {}

        return jsonify({
            'success': True,
            'data': keyword_dict
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@iframe_healthie_provider_tab_medications_bp.route('/healthie/iframe_provider_tab/medications/create_common_medication', methods=['GET','POST'])
def iframe_healthie_provider_tab_create_common_medication():
    """
    Creates a common medication.
    """
    try:
        common_name = request.form.get('common_name')
        category = request.form.get('category')
        supercategory = request.form.get('supercategory')
        category_custom = request.form.get('category_custom')
        supercategory_custom = request.form.get('supercategory_custom')

        new_common_medication = CommonMedication(
            common_name=common_name,
            category=category,
            supercategory=supercategory,
            category_custom=category_custom,
            supercategory_custom=supercategory_custom
        )

        response = create_common_medication(new_common_medication)

        if response['log']['success']:
            return jsonify({
                'success': True,
                'common_medication_id': response['common_medication_id']
            })
        else:
            return jsonify({
                'success': False,
                'common_medication_id': None,
                'error': response['log']['error']
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'common_medication_id': None,
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
        comment = request.form.get('comment')
        directions = request.form.get('directions')

        common_medication_id = request.form.get('common_medication_id')
        dosing_schedule_rule = request.form.get('dosing_schedule_rule')
        total_daily_dosage = request.form.get('total_daily_dosage')
        dosage_amount = request.form.get('dosage_amount')
        dosage_unit = request.form.get('dosage_unit')
        dose_count = request.form.get('dose_count')
        frequency = request.form.get('frequency')
        dosing_interval = request.form.get('dosing_interval')
        time_of_day = request.form.get('time_of_day')
        day_period = request.form.getlist('day_period')
        day_of_week = request.form.getlist('day_of_week')

        medication_record = MedicationRecord(
            syntrillo_internal_key=str(syntrillo_internal_key),
            medication_name=medication_name,
            is_active=is_active,
            start_date=start_date,
            end_date=end_date,
            comment=comment,
            directions=directions,
            mirrored=mirrored,
            common_medication_id=common_medication_id,
            dosing_schedule_rule=dosing_schedule_rule,
            total_daily_dosage=total_daily_dosage,
            dosage_amount=dosage_amount,
            dosage_unit=dosage_unit,
            frequency=frequency,
            dose_count=dose_count,
            dosing_interval=dosing_interval,
            time_of_day=time_of_day,
            day_period=day_period,
            day_of_week=day_of_week,
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
        syntrillo_medication_id = request.form.get('id')

        updated_fields = {}

        for field in [
            'medication_name', 'dosage_option_id', 'mirrored', 'is_active',
            'start_date', 'end_date', 'comment', 'directions', 'delivery_method',
            'common_medication_id', 'dosing_schedule_rule', 'total_daily_dosage',
            'dosage_amount', 'dosage_unit', 'dose_count', 'frequency',
            'dosing_interval', 'time_of_day', 'day_period', 'day_of_week'
        ]:
            value = request.form.get(field)
            if value is not None:
                updated_fields[field] = value

        db_manager = SyntrilloMedicationsDatabaseQueries()

        response, log = db_manager.update_patient_medication(
            id=syntrillo_medication_id,
            updated_fields=updated_fields
        )

        if log['success']:
            medications, log = db_manager.get_patient_medications(syntrillo_internal_key)

        return jsonify({
            'success': True,
            'data': medications
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
        medication_id = request.form.get('id')
        healthie_medication_id = request.form.get('healthie_medication_id')
        delete_medication(syntrillo_internal_key, medication_id, healthie_medication_id)

        return jsonify({
            'success': True,
            'data': medication_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
