# Path: ./apps/PythonAnywhere/website/routes/healthie/iframe_provider_sidebar/id_dump.py
from flask import Blueprint, render_template, request, jsonify, abort, send_file

import json
import os
import io

# python.analysis.extraPaths added into .vscode/settings.json
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.system.iframe_validator import IframeValidator
from syntrillo.data_structures.healthie_dump import DataStructureHealthieDump

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

# ========================= DOWNLOAD ENDPOINT ==========================

@iframe_healthie_provider_sidebar_id_dump_bp.route('/download/data_structure_dump/', methods=['POST'])
def download_data_structure_dump():
    """
    This endpoint is used to download a dump of questionnaires structures.

    """

    # Retrieve the JSON data from the POST request
    data_post_request = request.form.to_dict()

    # --------------------------------------------------------

    # dump_data_type : either 'json' or 'xlsx'
    dump_data_type = data_post_request.get('dump_data_type')

    # get the file from the database
    manager = DataStructureHealthieDump()

    dump_bytes, full_name, mimetype, log = manager.retrieve_dump(dump_data_type=dump_data_type)

    if dump_bytes is None or not log.get('success', False):
        abort(404)

    else:
        # Wrap the bytes data in an io.BytesIO object
        dump_file = io.BytesIO(dump_bytes)

        response = send_file(
            dump_file,
            as_attachment=True,
            download_name=full_name,
            mimetype=mimetype, # 'application/json' or 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        # Now, add the response headers to include filename and mimetype
        response.headers['Content-Type'] = mimetype
        response.headers['X-Filename'] = full_name
        response.headers['X-Mimetype'] = mimetype

        # Create a JSON string from the log without any newlines
        log_json = json.dumps(log)
        response.headers['X-Log'] = log_json

        return response



# ========================= ENDPOINTS ==========================

