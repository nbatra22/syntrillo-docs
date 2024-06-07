# Path: ./apps/PythonAnywhere/website/healthie/iframe_provider_tab/onboarding.py
from flask import Blueprint, render_template

iframe_healthie_provider_tab_onboarding_bp = Blueprint('iframe_healthie_provider_tab_onboarding_bp', __name__)

@iframe_healthie_provider_tab_onboarding_bp.route('/healthie/iframe_provider_tab/onboarding')
def iframe_healthie_provider_tab_onboarding():
    return render_template('healthie/iframe_provider_tab/onboarding.html')

