from flask import Blueprint, render_template, request, jsonify

# python.analysis.extraPaths added into .vscode/settings.json
from syntrillo.api_healthie.utils import HealthieUtils

iframe_healthie_provider_sidebar_status_bp = Blueprint('iframe_healthie_provider_sidebar_status_bp', __name__)

# ========================= HTML PAGE ==========================

@iframe_healthie_provider_sidebar_status_bp.route('/healthie/iframe_provider_sidebar/status', methods=['POST'])
def iframe_healthie_provider_sidebar_status():
    """
    This endpoint is used to display the status page in the provider sidebar iframe.
    It is called by the healthie_iframe_provider_sidebar index.html
    """

    healthie_provider_id = request.form.get('healthie_provider_id')

    # --------------------------------------------------------------------

    # Create an instance of HealthieAPI with the provided API key and organization
    utils_api = HealthieUtils()

    # Example: Get organization details
    organization_details = utils_api.get_organization_details()

    return render_template(
        'healthie/iframe_provider_sidebar/status.html',
        healthie_provider_id=healthie_provider_id,
        organization_details=organization_details,
        )

# ========================= ENDPOINTS ==========================

