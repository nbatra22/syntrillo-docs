# Path: ./apps/PythonAnywhere/website/routes/healthie/iframe_provider_sidebar/index.py

from flask import Blueprint, request, jsonify, render_template, abort
import json
import random

from syntrillo.system.iframe_validator import IframeValidator

# python.analysis.extraPaths added into .vscode/settings.json

# -------------------------------------------------

iframe_healthie_provider_sidebar_index_bp = Blueprint('iframe_healthie_provider_sidebar_index_bp', __name__)

@iframe_healthie_provider_sidebar_index_bp.route('/iframe_healthie_provider_sidebar', methods=['GET'])
def iframe_healthie_provider_sidebar_index():
    """
    iframe displayed in :

    Provider portal, extra sidebar item:
        hl_current_user_id: 1033222 # that's the provider ID
        referrer_url: https://securestaging.gethealthie.com/


    """

    # --------------------------------------------------------------------
    # Check if the request origin/referer is allowed
    iframe_validator = IframeValidator()
    iframe_valid, iframe_log = iframe_validator.is_request_allowed(request)
    if not iframe_valid:
        pass
        # abort(403, description="Access Denied: Unauthorized Embedding\n" + json.dumps(iframe_log))

    # --------------------------------------------------------------------
    # Retrieve the JSON data from the GET request
    data_get_request = request.args.to_dict()

    # Extract hl_current_user_id from data_get_request
    # here it is the provider id
    healthie_provider_id = data_get_request.get('hl_current_user_id')

    if healthie_provider_id is None:
        healthie_provider_id = "1033222" # "-1"


    return render_template('healthie/iframe_provider_sidebar/index.html',
                           healthie_provider_id=healthie_provider_id,
                           iframe_log=iframe_log
                           )