from flask import Blueprint, render_template, request, jsonify

# python.analysis.extraPaths added into .vscode/settings.json


iframe_healthie_provider_sidebar_system_bp = Blueprint('iframe_healthie_provider_sidebar_system_bp', __name__)

# ========================= HTML PAGE ==========================

@iframe_healthie_provider_sidebar_system_bp.route('/healthie/iframe_provider_sidebar/system', methods=['POST'])
def iframe_healthie_provider_sidebar_system():
    """
    This endpoint is used to display the system page in the provider sidebar iframe.
    It is called by the healthie_iframe_provider_sidebar index.html
    """

    healthie_provider_id = request.form.get('healthie_provider_id')

    # --------------------------------------------------------------------


    return render_template(
        'healthie/iframe_provider_sidebar/system.html',
        healthie_provider_id=healthie_provider_id,
        )

# ========================= ENDPOINTS ==========================

