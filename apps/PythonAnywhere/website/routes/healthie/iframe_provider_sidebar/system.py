# Path: ./apps/PythonAnywhere/website/routes/healthie/iframe_provider_sidebar/system.py
from flask import Blueprint, render_template, request, jsonify

from syntrillo.system.iframe_validator import IframeValidator


iframe_healthie_provider_sidebar_system_bp = Blueprint('iframe_healthie_provider_sidebar_system_bp', __name__)

# ========================= HTML PAGE ==========================

@iframe_healthie_provider_sidebar_system_bp.route('/healthie/iframe_provider_sidebar/system', methods=['POST'])
def iframe_healthie_provider_sidebar_system():
    """
    This endpoint is used to display the system page in the provider sidebar iframe.
    It is called by the healthie_iframe_provider_sidebar index.html
    """

    # --------------------------------------------------------------------
    # Check if the request origin/referer is allowed
    iframe_validator = IframeValidator()
    iframe_valid, iframe_log = iframe_validator.is_request_allowed(request)
    if not iframe_valid:
        pass
        # abort(403, description="Access Denied: Unauthorized Embedding\n" + json.dumps(iframe_log))


    # --------------------------------------------------------------------

    healthie_provider_id = request.form.get('healthie_provider_id')

    # --------------------------------------------------------------------


    return render_template(
        'healthie/iframe_provider_sidebar/system.html',
        healthie_provider_id=healthie_provider_id,
        iframe_log=iframe_log
        )

# ========================= ENDPOINTS ==========================

