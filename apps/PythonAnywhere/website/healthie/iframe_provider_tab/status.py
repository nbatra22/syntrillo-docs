# Path: ./apps/PythonAnywhere/website/healthie/iframe_provider_tab/status.py
from flask import Blueprint, render_template

iframe_healthie_provider_tab_status_bp = Blueprint('iframe_healthie_provider_tab_status_bp', __name__)

@iframe_healthie_provider_tab_status_bp.route('/healthie/iframe_provider_tab/status')
def iframe_healthie_provider_tab_status():
    return render_template('healthie/iframe_provider_tab/status.html')

