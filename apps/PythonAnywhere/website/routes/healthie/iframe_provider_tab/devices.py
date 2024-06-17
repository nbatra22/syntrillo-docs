# Path: ./apps/PythonAnywhere/website/routes/healthie/iframe_provider_tab/devices.py
from flask import Blueprint, render_template, request, jsonify

import json
import datetime

from .post_management import PostManager
from syntrillo.patient_initialization.accounts_pairing import AccountsPairing
from syntrillo.patient_initialization.order_tenovi_devices import OrderTenoviDevices
from syntrillo.api_healthie.utils import HealthieUtils


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

    gateway_id = None
    for device in paired_devices:
        # get gateway id : TODO : manage if several gateways
        gateway_id = device['device']['hardware_uuid_formatted']
        # Format dates before passing to template
        if 'created' in device['device']:
            device['device']['created_USformat'] = format_date(device['device']['created'])

    if gateway_id is None:
        gateway_checked = ""
    else:
        gateway_checked = "checked"

    # unroll order new devices form if it looks everything is in order
    if len(paired_devices) >= 3 :
        unroll_order_new_devices_form = False
    else:
        unroll_order_new_devices_form = True

    # --------------------------------------------------------------------
    # get user PII
    healthie_utils = HealthieUtils()
    user_pii = healthie_utils.get_user_from_id(post_manager.pseudonyms['healthie_user_id'])

    # Check if user_pii has locations and get the number of locations
    n_user_locations = len(user_pii['locations']) if 'locations' in user_pii and user_pii['locations'] else 0


    return render_template('healthie/iframe_provider_tab/devices.html',
                           temporary_lookup_code=post_manager.temporary_lookup_code,
                           healthie_provider_id=post_manager.healthie_provider_id,
                           paired_devices=paired_devices,
                           gateway_id=gateway_id,
                           gateway_checked=gateway_checked,
                           user_pii=user_pii,
                           n_user_locations=n_user_locations,
                           unroll_order_new_devices_form=unroll_order_new_devices_form,
                           )

# ========================= ENDPOINTS ==========================

def _checkbox_to_bool(checkbox):
    if checkbox is None:
        return False
    else:
        return True

@iframe_healthie_provider_tab_devices_bp.route('/healthie/iframe_provider_tab/devices/tenovi_order_new_devices_form', methods=['POST'])
def tenovi_order_new_devices_form():
    """
    This endpoint orders new devices from Tenovi API.

    """

    # get all pseudonyms from post temporary identifier
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # --------------------------------------------------------------------
    # get posted data

    include_gateway_id = _checkbox_to_bool(request.form.get('include_gateway_id'))

    gateway_id = request.form.get('gateway_id')

    device_bpm_large = _checkbox_to_bool(request.form.get('device_bpm_large'))
    device_bpm_small = _checkbox_to_bool(request.form.get('device_bpm_small'))
    device_pillbox = _checkbox_to_bool(request.form.get('device_pillbox'))
    device_watch = _checkbox_to_bool(request.form.get('device_watch'))

    flag_devices = _checkbox_to_bool(request.form.get('flag_devices'))

    location_index = request.form.get('location_index')
    if location_index is None:
        location_index = 0

    sms_opt_in = _checkbox_to_bool(request.form.get('sms_opt_in'))

    # --------------------------------------------------------------------
    # order selected devices and pair them with healthie identifier and our pseudo code
    order = OrderTenoviDevices(post_manager.syntrillo_internal_key)

    log_place_order = order.place_order(
        devices_names=[
            'Tenovi BPM - L' if device_bpm_large else None,
            'Tenovi BPM - S' if device_bpm_small else None,
            'Tenovi Watch' if device_watch else None,
            'Tenovi Pillbox' if device_pillbox else None,
        ],
        gateway_id=gateway_id if include_gateway_id else None,
        sms_opt_in=sms_opt_in,
        healthie_location_index=int(location_index),
        flag_devices=flag_devices,
    )

    # --------------------------------------------------------------------
    # generate log
    #   : log.success must be provided : used by HTML to display success or error message

    success = log_place_order['success']

    log_form = {
        "include_gateway_id": include_gateway_id,
        "gateway_id": gateway_id,
        "device_bpm_large": device_bpm_large,
        "device_bpm_small": device_bpm_small,
        "device_pillbox": device_pillbox,
        "device_watch": device_watch,
        "location_index": location_index,
        "sms_opt_in": sms_opt_in,
    }

    if success:
        log = {
            "success": True,
            "message": "Devices ordered successfully",
            "log_form": log_form,
            "log_place_order": log_place_order,
        }
    else:
        log = {
            "success": False,
            "message": "Error while ordering devices",
            "request": request.form,
            "log_form": log_form,
            "log_place_order": log_place_order,
        }

    return jsonify( log ), 200

