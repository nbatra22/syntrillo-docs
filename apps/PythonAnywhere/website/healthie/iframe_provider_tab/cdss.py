# Path: ./apps/PythonAnywhere/website/healthie/iframe_provider_tab/cdss.py
from flask import Blueprint, render_template

iframe_healthie_provider_tab_cdss_bp = Blueprint('iframe_healthie_provider_tab_cdss_bp', __name__)

@iframe_healthie_provider_tab_cdss_bp.route('/healthie/iframe_provider_tab/cdss')
def iframe_healthie_provider_tab_cdss():
    return render_template('healthie/iframe_provider_tab/cdss.html')

