# Path: ./apps/PythonAnywhere/website/routes/healthie/iframe_provider_tab/system_devices.py
from flask import Blueprint, render_template, request, jsonify

import json

from .post_management import PostManager
from syntrillo.patient_initialization.accounts_pairing import AccountsPairing
from syntrillo.remote_monitoring.data_sync import RemoteMonitoringDataSync
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.api_healthie.metrics import HealthieMetrics

iframe_healthie_provider_tab_system_devices_bp = Blueprint('iframe_healthie_provider_tab_system_devices_bp', __name__)

# ========================= HTML PAGE ==========================

@iframe_healthie_provider_tab_system_devices_bp.route('/healthie/iframe_provider_tab/system_devices', methods=['POST'])
def iframe_healthie_provider_tab_system_devices():
    """
    This endpoint is used to display the devices page in the provider tab iframe.
    It is called by the healthie_iframe_provider_tab index.html
    """

    # get all pseudonyms from post temporary identifier
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_index_post(request)

    # deal with patients not registered at Syntrillo
    if post_manager.patient_not_registered_at_syntrillo:
        return render_template('healthie/iframe_provider_tab/patient_not_registered.html')

    # --------------------------------------------------------------------
    # get paired devices from Tenovi API
    paired_devices = AccountsPairing.get_paired_devices(
        syntrillo_internal_key=post_manager.syntrillo_internal_key,
        add_syntrillo_database_stats=True,
        add_tenovi_latest_record_timestamp=True,
        )


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

    # get all pseudonyms from post temporary identifier
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # sync
    sync = RemoteMonitoringDataSync(post_manager.syntrillo_internal_key)

    overall_log = {
        "success": True,
        "number_of_records_inserted__tenovi_to_syntrillo": 0,
        "number_of_records_inserted__syntrillo_to_healthie": 0,
    }

    # sync data between Tenovi and Syntrillo

    log1 = sync.sync_tenovi_to_syntrillo()
    overall_log['tenovi_to_syntrillo'] = log1

    if not log1['success']:
        overall_log['success'] = False

    else:
        overall_log['number_of_records_inserted__tenovi_to_syntrillo'] = log1['number_of_records_inserted']

        log2 = sync.sync_syntrillo_to_healthie()
        overall_log['syntrillo_to_healthie'] = log2

        if not log2['success']:
            overall_log['success'] = False
        else:
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


