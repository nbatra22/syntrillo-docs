# Path: ./apps/PythonAnywhere/website/healthie/iframe_provider_tab/care_plan.py
from flask import Blueprint, render_template, request

from .post_management import PostManager

iframe_healthie_provider_tab_care_plan_bp = Blueprint('iframe_healthie_provider_tab_care_plan_bp', __name__)

@iframe_healthie_provider_tab_care_plan_bp.route('/healthie/iframe_provider_tab/care_plan', methods=['POST'])
def iframe_healthie_provider_tab_care_plan():
    """
    This endpoint is used to display the care plan page in the provider tab iframe.
    """
    # get all pseudonyms from post temporary identifier
    post_manager = PostManager(request)

    # deal with patients not registered at Syntrillo
    if post_manager.patient_not_registered_at_syntrillo:
        return render_template('healthie/iframe_provider_tab/patient_not_registered.html')

    # --------------------------------------------------------------------

    return render_template('healthie/iframe_provider_tab/care_plan.html')

