# Path: ./apps/PythonAnywhere/website/routes/healthie/iframe_provider_sidebar/id_dump.py
from flask import Blueprint, render_template, request, jsonify, abort

# python.analysis.extraPaths added into .vscode/settings.json
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.system.iframe_validator import IframeValidator

iframe_healthie_provider_sidebar_id_dump_bp = Blueprint('iframe_healthie_provider_sidebar_id_dump_bp', __name__)

# ========================= HTML PAGE ==========================

@iframe_healthie_provider_sidebar_id_dump_bp.route('/healthie/iframe_provider_sidebar/id_dump', methods=['POST'])
def iframe_healthie_provider_sidebar_id_dump():
    """
    This endpoint is used to dump IDs of questionnaires in the provider sidebar iframe.
    It is called by the healthie_iframe_provider_sidebar index.html
    """

    # --------------------------------------------------------------------
    # Check if the request origin/referer is allowed
    iframe_validator = IframeValidator()
    iframe_valid, iframe_log = iframe_validator.is_request_allowed(request)
    if not iframe_valid:
        abort(403, description="Access Denied")

    # --------------------------------------------------------------------
    healthie_provider_id = request.form.get('healthie_provider_id')

    # --------------------------------------------------------------------

    # Create an instance of HealthieAPI with the provided API key and organization
    utils_api = HealthieUtils()

    # Example: Get organization details
    organization_details = utils_api.get_organization_details()

    return render_template(
        'healthie/iframe_provider_sidebar/id_dump.html',
        healthie_provider_id=healthie_provider_id,
        organization_details=organization_details,
        )

# ========================= ENDPOINTS ==========================

