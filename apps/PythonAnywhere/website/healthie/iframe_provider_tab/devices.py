# Path: ./apps/PythonAnywhere/website/healthie/iframe_provider_tab/devices.py
from flask import Blueprint, render_template, request

import time

from .post_management import PostManager
from syntrillo.patient_initialization.accounts_pairing import AccountsPairing

iframe_healthie_provider_tab_devices_bp = Blueprint('iframe_healthie_provider_tab_devices_bp', __name__)

@iframe_healthie_provider_tab_devices_bp.route('/healthie/iframe_provider_tab/devices', methods=['POST'])
def iframe_healthie_provider_tab_devices():
    """
    This endpoint is used to display the devices page in the provider tab iframe.
    """

    # get all pseudonyms from post temporary identifier
    post_manager = PostManager(request)

    # deal with patients not registered at Syntrillo
    if post_manager.patient_not_registered_at_syntrillo:
        return render_template('healthie/iframe_provider_tab/patient_not_registered.html')

    # --------------------------------------------------------------------
    # get paired devices from Tenovi API
    paired_devices = AccountsPairing.get_paired_devices(syntrillo_internal_key=post_manager.syntrillo_internal_key)


    return render_template('healthie/iframe_provider_tab/devices.html')
