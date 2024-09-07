# Path: ./apps/PythonAnywhere/website/routes/healthie/iframe_provider_tab/system_devices.py
from flask import Blueprint, render_template, request, jsonify, abort

import json
from datetime import datetime, timedelta

from .post_management import PostManager
from syntrillo.patient_initialization.accounts_pairing import AccountsPairing
from syntrillo.remote_monitoring.data_sync import RemoteMonitoringDataSync
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.api_healthie.metrics import HealthieMetrics
from syntrillo.remote_monitoring.tenovi_dummy_data_generator import TenoviDummyDataGenerator
from syntrillo.system.iframe_validator import IframeValidator

iframe_healthie_provider_tab_system_devices_bp = Blueprint('iframe_healthie_provider_tab_system_devices_bp', __name__)

# ========================= HTML PAGE ==========================

from aws_lambda_powertools import Logger
logger = Logger(service="SYSTEM_DEVICES")

# from aws_xray_sdk.core import patch_all, xray_recorder
# patch_all()

@iframe_healthie_provider_tab_system_devices_bp.route('/healthie/iframe_provider_tab/system_devices', methods=['POST'])
# @xray_recorder.capture('iframe_healthie_provider_tab_system_devices')
def iframe_healthie_provider_tab_system_devices():
    """
    This endpoint is used to display the devices page in the provider tab iframe.
    It is called by the healthie_iframe_provider_tab index.html
    """

    # --------------------------------------------------------------------
    # Check if the request origin/referer is allowed
    iframe_validator = IframeValidator()
    iframe_valid, iframe_log = iframe_validator.is_request_allowed(request)
    if not iframe_valid:
        abort(403, description="Access Denied")

    # --------------------------------------------------------------------
    # get all pseudonyms from post temporary identifier
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_index_post(request)

    # deal with patients not registered at Syntrillo
    if post_manager.patient_not_registered_at_syntrillo:
        # log the healthie_user_id of the patient not registered to allow for further investigation
        logger.warning(f"[SYSTEM_DEVICES] <PATIENT NOT REGISTERED> healthie_user_id {post_manager.posted_healthie_user_id}")
        # render the patient_not_registered.html template
        return render_template('healthie/iframe_provider_tab/patient_not_registered.html')

    # --------------------------------------------------------------------
    # get paired devices from Tenovi API
    paired_devices = AccountsPairing.get_paired_devices(
        syntrillo_internal_key=post_manager.syntrillo_internal_key,
        add_syntrillo_database_stats=True,
        add_tenovi_latest_record_timestamp=True,
        )

    # Minimal logging
    if paired_devices is not None:
        logger.info(f"[SYSTEM_DEVICES] <PAIRED DEVICES RETRIEVED> paired_devices_ids {[entry['id'] for entry in paired_devices]} <FOR> temporary_lookup_code {post_manager.temporary_lookup_code }")

    return render_template('healthie/iframe_provider_tab/system_devices.html',
                           temporary_lookup_code=post_manager.temporary_lookup_code,
                           healthie_provider_id=post_manager.healthie_provider_id,
                           paired_devices=paired_devices,
                           )

# ========================= ENDPOINTS ==========================

@iframe_healthie_provider_tab_system_devices_bp.route('/healthie/iframe_provider_tab/system_devices/tenovi_generate_temporary_pairing_code_form', methods=['POST'])
def tenovi_generate_temporary_pairing_code_form():
    """
    This endpoint generates a pairing code to be entered in the Tenovi platform 'Patient ID' field by the study coordinator.

    Returns a tuple with the following elements:
        log (dict): log of the operation, with 'success' key, used by the frontend to check if the operation was successful
        200 (int): status code

    """

    # get all pseudonyms from post temporary identifier
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # Call AccountsPairing.create_and_return_unique_temporary_pseudo_code
    accounts_pairing = AccountsPairing(post_manager.syntrillo_internal_key)
    temporary_tenovi_pseudo_code = accounts_pairing.create_and_return_unique_temporary_pseudo_code()

    if temporary_tenovi_pseudo_code is None:
        log = {
            "success": False,
            "message": "Error: Temporary Pseudo Code for Tenovi pairing not generated",
            'temporary_tenovi_pseudo_code': None
        }
    else:
        log = {
            "success": True,
            "message": "Temporary Pseudo Code for Tenovi pairing generated successfully",
            'temporary_tenovi_pseudo_code': temporary_tenovi_pseudo_code
        }

    return jsonify( log ), 200


@iframe_healthie_provider_tab_system_devices_bp.route('/healthie/iframe_provider_tab/system_devices/tenovi_pair_devices_form', methods=['POST'])
def tenovi_pair_devices_form():
    """
    This endpoint pairs the devices using the temporary tenovi pseudo code.

    Returns a tuple with the following elements:
        log (dict): log of the operation, with 'success' key, used by the frontend to check if the operation was successful
        200 (int): status code

    """

    # get all pseudonyms from post temporary identifier
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # pair devices using the temporary pseudo codes
    pairing = AccountsPairing(post_manager.syntrillo_internal_key)
    log = pairing.pair_devices_using_temporary_pseudo_code()

    return jsonify( log ), 200


@iframe_healthie_provider_tab_system_devices_bp.route('/healthie/iframe_provider_tab/system_devices/sync_measurements_form', methods=['POST'])
def sync_measurements_form():
    """
    This endpoint sync measurements for this patient. Tenovi -> Syntrillo -> Healthie

    Returns a tuple with the following elements:
        log (dict): log of the operation, with 'success' key, used by the frontend to check if the operation was successful
        200 (int): status code

    """

    # --------------------------------------------------------------------
    # get all pseudonyms from post temporary identifier
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # --------------------------------------------------------------------
    # get data from the form
    sync_measurements_form_what_to_sync = request.form.to_dict().get('sync_measurements_form_what_to_sync')

    sync_tenovi_to_syntrillo = False
    sync_syntrillo_to_healthie = False
    if sync_measurements_form_what_to_sync == "sync_tenovi_to_syntrillo":
        sync_tenovi_to_syntrillo = True
    elif sync_measurements_form_what_to_sync == "sync_syntrillo_to_healthie":
        sync_syntrillo_to_healthie = True
    elif sync_measurements_form_what_to_sync == "sync_both":
        sync_tenovi_to_syntrillo = True
        sync_syntrillo_to_healthie = True

    # --------------------------------------------------------------------
    # sync
    sync = RemoteMonitoringDataSync(post_manager.syntrillo_internal_key)

    # TODO : move this section to the sync method
    overall_log = {
        "success": True,
        "number_of_records_inserted__tenovi_to_syntrillo": 0,
        "number_of_records_inserted__syntrillo_to_healthie": 0,
    }

    # sync tenovi to syntrillo
    if sync_tenovi_to_syntrillo:
        log1 = sync.sync_tenovi_to_syntrillo()
        overall_log['tenovi_to_syntrillo'] = log1
        overall_log['success'] = overall_log['success'] and log1['full_success']

        if log1['number_of_records_inserted'] is not None:
            overall_log['number_of_records_inserted__tenovi_to_syntrillo'] = log1['number_of_records_inserted']

    # sync syntrillo to healthie
    if sync_syntrillo_to_healthie:
        log2 = sync.sync_syntrillo_to_healthie()
        overall_log['syntrillo_to_healthie'] = log2
        overall_log['success'] = overall_log['success'] and log2['success']

        if log2['number_of_records_inserted'] is not None:
            overall_log['number_of_records_inserted__syntrillo_to_healthie'] = log2['number_of_records_inserted']


    return jsonify( overall_log ), 200


@iframe_healthie_provider_tab_system_devices_bp.route('/healthie/iframe_provider_tab/system_devices/delete_syntrillo_measurements_records_form', methods=['POST'])
def delete_syntrillo_measurements_records_form():
    """
    This endpoint deletes all measurements records from Syntrillo for this patient.

    Returns a tuple with the following elements:
        log (dict): log of the operation, with 'success' key, used by the frontend to check if the operation was successful
        200 (int): status code

    """

    # get all pseudonyms from post temporary identifier
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # connect to the remote monitoring database for this patient
    db_manager = SyntrilloDatabaseManager(post_manager.syntrillo_internal_key)

    # delete all records from all devices
    log = db_manager.delete_records()

    return jsonify( log ), 200


@iframe_healthie_provider_tab_system_devices_bp.route('/healthie/iframe_provider_tab/system_devices/delete_healthie_measurements_metrics_form', methods=['POST'])
def delete_healthie_measurements_metrics_form():
    """
    This endpoint deletes all metrics from Healthie for this patient.

    Returns a tuple with the following elements:
        log (dict): log of the operation, with 'success' key, used by the frontend to check if the operation was successful
        200 (int): status code

    """

    # get all pseudonyms from post temporary identifier
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # get healthie user id
    healthie_user_id = post_manager.pseudonyms['healthie_user_id']

    # connect to Healthie metrics
    metrics = HealthieMetrics()

    # remove all metrics
    log1 = metrics.remove_metric_data(user_id=healthie_user_id, category=HealthieMetrics.HEALTHIE_METRICS_AVERAGE_PULSE_CATEGORY)
    log2 = metrics.remove_metric_data(user_id=healthie_user_id, category=HealthieMetrics.HEALTHIE_METRICS_BLOOD_PRESSURE_CATEGORY)
    log3 = metrics.remove_metric_data(user_id=healthie_user_id, category=HealthieMetrics.HEALTHIE_METRICS_HOURS_OF_SLEEP_CATEGORY)
    log4 = metrics.remove_metric_data(user_id=healthie_user_id, category=HealthieMetrics.HEALTHIE_METRICS_MAXIMUM_PULSE_CATEGORY)
    log5 = metrics.remove_metric_data(user_id=healthie_user_id, category=HealthieMetrics.HEALTHIE_METRICS_PULSE_CATEGORY)
    log6 = metrics.remove_metric_data(user_id=healthie_user_id, category=HealthieMetrics.HEALTHIE_METRICS_TOTAL_STEPS_PER_DAY_CATEGORY)

    # overall log
    overall_log = {}

    overall_log['success'] = log1['success'] and log2['success'] and log3['success'] and log4['success'] and log5['success'] and log6['success']
    overall_log['log1'] = log1
    overall_log['log2'] = log2
    overall_log['log3'] = log3
    overall_log['log4'] = log4
    overall_log['log5'] = log5
    overall_log['log6'] = log6

    return jsonify( overall_log ), 200


def _checkbox_to_bool(checkbox):
    if checkbox is None:
        return False
    else:
        return True

# data_generator = TenoviDummyDataGenerator(entry["syntrillo_internal_key"],
@iframe_healthie_provider_tab_system_devices_bp.route('/healthie/iframe_provider_tab/system_devices/tenovi_dummy_data_generator_form', methods=['POST'])
def tenovi_dummy_data_generator_form():
    """
    This endpoint generates dummy data for this patient.

    Returns a tuple with the following elements:
        log (dict): log of the operation, with 'success' key, used by the frontend to check if the operation was successful
        200 (int): status code
    """

    # get all pseudonyms from post temporary identifier
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # --------------------------------------------------------------------
    success = True
    log = {
        "success": True,
    }


    # get posted data
    sync_and_reload = _checkbox_to_bool(request.form.get('sync_and_reload'))
    log['must_reload'] = sync_and_reload

    date_start_ago = request.form.get('date_start_ago')
    date_end_ago = request.form.get('date_end_ago')

    blood_pressure_state = request.form.get('blood_pressure_state')
    heart_rate_state = request.form.get('heart_rate_state')
    steps_state = request.form.get('steps_state')
    medication_adherence_state = request.form.get('medication_adherence_state')
    medication_expected_pattern = request.form.get('medication_expected_pattern')

    irregular_heartbeat = _checkbox_to_bool(request.form.get('has_arrhythmia'))

    # ---------------------
    # manage dates
    today = datetime.today()

    # ---- start date ----
    if date_start_ago == "one-week-ago":
        date_start = today - timedelta(weeks=1)

    elif date_start_ago == "one-month-ago":
        date_start = today - timedelta(weeks=4)

    elif date_start_ago == "two-months-ago":
        date_start = today - timedelta(weeks=8)

    elif date_start_ago == "three-months-ago":
        date_start = today - timedelta(weeks=12)

    elif date_start_ago == "four-months-ago":
        date_start = today - timedelta(weeks=16)

    elif date_start_ago == "five-months-ago":
        date_start = today - timedelta(weeks=20)

    elif date_start_ago == "six-months-ago":
        date_start = today - timedelta(weeks=24)

    elif date_start_ago == "one-year-ago":
        date_start = today - timedelta(weeks=52)

    else:
        success = False
        log['success'] = False
        log['error'] = "Invalid date_start_ago: " + date_start_ago

    # ---- end date ----
    if date_end_ago == "today":
        date_end = today

    elif date_end_ago == "one-week-ago":
        date_end = today - timedelta(weeks=1)

    elif date_end_ago == "one-month-ago":
        date_end = today - timedelta(weeks=4)

    elif date_end_ago == "two-months-ago":
        date_end = today - timedelta(weeks=8)

    elif date_end_ago == "three-months-ago":
        date_end = today - timedelta(weeks=12)

    elif date_end_ago == "four-months-ago":
        date_end = today - timedelta(weeks=16)

    elif date_end_ago == "five-months-ago":
        date_end = today - timedelta(weeks=20)

    elif date_end_ago == "six-months-ago":
        date_end = today - timedelta(weeks=24)

    else:
        success = False
        log['success'] = False
        log['error'] = "Invalid date_end_ago: " + date_end_ago

    if success:
        # instantiate TenoviDummyDataGenerator
        data_generator = TenoviDummyDataGenerator(post_manager.syntrillo_internal_key)

        # set states
        data_generator.set_patient_state(
            patient_state_blood_pressure=blood_pressure_state,
            patient_state_heart_rate=heart_rate_state,
            patient_state_steps=steps_state,
            patient_state_medication_adherence = medication_adherence_state,
            patient_state_medication_expected_pattern = medication_expected_pattern,
            patient_state_irregular_heartbeat=irregular_heartbeat,
        )

        # generate dummy data
        data_generator.generate_all_devices_data_wrapup(
            date_start=date_start,
            date_end=date_end,
        )

        # sync and reload
        if sync_and_reload:
            sync = RemoteMonitoringDataSync(post_manager.syntrillo_internal_key)

            sync_log = sync.sync_syntrillo_to_healthie()

            if sync_log['success'] :
                log['number_of_records_inserted__syntrillo_to_healthie'] = sync_log['number_of_records_inserted']
            else:
                log['success'] = False
                log['sync_log_error'] = sync_log

    return jsonify( log ), 200

