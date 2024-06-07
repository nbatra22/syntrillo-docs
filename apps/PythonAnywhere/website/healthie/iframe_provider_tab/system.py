# Path: ./apps/PythonAnywhere/website/healthie/iframe_provider_tab/system.py
from flask import Blueprint, render_template

iframe_healthie_provider_tab_system_bp = Blueprint('iframe_healthie_provider_tab_system_bp', __name__)

@iframe_healthie_provider_tab_system_bp.route('/healthie/iframe_provider_tab/system')
def iframe_healthie_provider_tab_system():
    return render_template('healthie/iframe_provider_tab/system.html')

