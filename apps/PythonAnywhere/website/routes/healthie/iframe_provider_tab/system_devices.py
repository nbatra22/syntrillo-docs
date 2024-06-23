# Path: ./apps/PythonAnywhere/website/routes/healthie/iframe_provider_tab/system_devices.py
from flask import Blueprint, render_template, request, jsonify

import json

from .post_management import PostManager
from syntrillo.patient_initialization.accounts_pairing import AccountsPairing

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

    """

    # get all pseudonyms from post temporary identifier
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # pair devices using the temporary pseudo codes
    pairing = AccountsPairing(post_manager.syntrillo_internal_key)
    log = pairing.pair_devices_using_temporary_pseudo_code()

    return jsonify( log ), 200


