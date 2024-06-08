# Path: ./apps/PythonAnywhere/website/healthie/iframe_provider_tab/onboarding.py
from flask import Blueprint, render_template, request

iframe_healthie_provider_tab_onboarding_bp = Blueprint('iframe_healthie_provider_tab_onboarding_bp', __name__)

@iframe_healthie_provider_tab_onboarding_bp.route('/healthie/iframe_provider_tab/onboarding', methods=['POST'])
def iframe_healthie_provider_tab_onboarding():
    """
    This endpoint is used to display the onboarding page in the provider tab iframe.
    """
    # --------------------------------------------------------------------
    # Retrieve the form data from the POST request
    #   : these are passed from the healthie_iframe_provider_tab index.html
    #   : healthie_user_id, is None, unless in panic mode
    healthie_provider_id = request.form.get('healthie_provider_id')
    healthie_user_id = request.form.get('healthie_user_id')
    temporary_lookup_code = request.form.get('temporary_lookup_code')
    patient_not_registered_at_syntrillo_str = request.form.get('patient_not_registered_at_syntrillo')
    patient_not_registered_at_syntrillo=(patient_not_registered_at_syntrillo_str == 'True')

    # deal with patients not registered at Syntrillo
    if patient_not_registered_at_syntrillo:
        return render_template('healthie/iframe_provider_tab/patient_not_registered.html')

    # --------------------------------------------------------------------

    return render_template('healthie/iframe_provider_tab/onboarding.html')

