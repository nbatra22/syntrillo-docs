# Path: ./apps/PythonAnywhere/website/healthie/iframe_provider_tab/devices.py
from flask import Blueprint, render_template, request, jsonify

import json
import datetime

from .post_management import PostManager
from syntrillo.patient_initialization.accounts_pairing import AccountsPairing
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.pseudonyms_management.temporary_lookup_codes_management import TemporaryLookUpCodesManagement

iframe_healthie_provider_tab_devices_bp = Blueprint('iframe_healthie_provider_tab_devices_bp', __name__)

# Helper function to format ISO date to US date format (MMM DD, YYYY)
def format_date(iso_date):
    date_obj = datetime.datetime.fromisoformat(iso_date.replace('Z', '+00:00'))  # Convert ISO date to datetime object
    return date_obj.strftime('%b %d, %Y')  # Format date as MMM DD, YYYY

# ========================= HTML PAGE ==========================

@iframe_healthie_provider_tab_devices_bp.route('/healthie/iframe_provider_tab/devices', methods=['POST'])
def iframe_healthie_provider_tab_devices():
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
    paired_devices = AccountsPairing.get_paired_devices(syntrillo_internal_key=post_manager.syntrillo_internal_key)

    # Format dates before passing to template
    for device in paired_devices:
        if 'created' in device['device']:
            device['device']['created_USformat'] = format_date(device['device']['created'])

    return render_template('healthie/iframe_provider_tab/devices.html',
                           temporary_lookup_code=post_manager.temporary_lookup_code,
                           healthie_provider_id=post_manager.healthie_provider_id,
                           paired_devices=paired_devices,
                           )

# ========================= ENDPOINTS ==========================

