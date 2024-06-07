# Path: ./apps/PythonAnywhere/website/healthie/iframe_provider_tab/devices.py
from flask import Blueprint, render_template

iframe_healthie_provider_tab_devices_bp = Blueprint('iframe_healthie_provider_tab_devices_bp', __name__)

@iframe_healthie_provider_tab_devices_bp.route('/healthie/iframe_provider_tab/devices')
def iframe_healthie_provider_tab_devices():
    return render_template('healthie/iframe_provider_tab/devices.html')

