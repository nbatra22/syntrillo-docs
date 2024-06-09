# Path: ./apps/PythonAnywhere/website/healthie/iframe_provider_tab/onboarding.py
from flask import Blueprint, render_template, request, jsonify

from .post_management import PostManager

from syntrillo.patient_onboarding.manager import PatientOnboardingManager

iframe_healthie_provider_tab_onboarding_bp = Blueprint('iframe_healthie_provider_tab_onboarding_bp', __name__)

# ========================= HTML PAGE ==========================

@iframe_healthie_provider_tab_onboarding_bp.route('/healthie/iframe_provider_tab/onboarding', methods=['POST'])
def iframe_healthie_provider_tab_onboarding():
    """
    This endpoint is used to display the onboarding page in the provider tab iframe.
    It is called by the healthie_iframe_provider_tab index.html
    """

    # get all pseudonyms from post temporary identifier
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_index_post(request)

    # deal with patients not registered at Syntrillo
    if post_manager.patient_not_registered_at_syntrillo:
        return render_template('healthie/iframe_provider_tab/patient_not_registered.html')

    # --------------------------------------------------------------------

    onboarding_manager = PatientOnboardingManager()
    patient_status = onboarding_manager.get_user_status(user_id=post_manager.pseudonyms['healthie_user_id'])
    inconsistencies = onboarding_manager.get_inconsistencies(user_id=post_manager.pseudonyms['healthie_user_id'])

    return render_template('healthie/iframe_provider_tab/onboarding.html',
                           patient_status=patient_status,
                           inconsistencies=inconsistencies,
                           )


# ========================= ENDPOINTS ==========================

@iframe_healthie_provider_tab_onboarding_bp.route('/healthie/iframe_provider_tab/onboarding/healthie_onboarding_generate_personalized_form', methods=['POST'])
def healthie_onboarding_generate_personalized_form():
    """


    """

    # get all pseudonyms from post temporary identifier
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    log = ""

    return jsonify( log ), 200