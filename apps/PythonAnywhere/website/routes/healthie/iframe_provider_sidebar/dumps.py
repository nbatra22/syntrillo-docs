# Path: ./apps/PythonAnywhere/website/routes/healthie/iframe_provider_sidebar/id_dump.py
from flask import Blueprint, render_template, request, jsonify, abort, send_file

import json
import os
import io

# python.analysis.extraPaths added into .vscode/settings.json
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.system.iframe_validator import IframeValidator
from syntrillo.data_structures.healthie_dump import DataStructureHealthieDump

iframe_healthie_provider_sidebar_dumps_bp = Blueprint('iframe_healthie_provider_sidebar_dumps_bp', __name__)

# ========================= HTML PAGE ==========================

@iframe_healthie_provider_sidebar_dumps_bp.route('/healthie/iframe_provider_sidebar/dumps', methods=['POST'])
def iframe_healthie_provider_sidebar_dumps():
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

    return render_template(
        'healthie/iframe_provider_sidebar/dumps.html',
        healthie_provider_id=healthie_provider_id,
        )

# ========================= DOWNLOAD ENDPOINT ==========================

@iframe_healthie_provider_sidebar_dumps_bp.route('/download/data_structure_dump/', methods=['POST'])
def download_data_structure_dump():
    """
    This endpoint is used to download a dump of questionnaires structures.

    """

    # Retrieve the JSON data from the POST request
    data_post_request = request.form.to_dict()

    # --------------------------------------------------------

    # dump_data_type : either 'json' or 'xlsx'
    dump_data_type = data_post_request.get('dump_data_type')

    # get options from the POST request
    include_labels = data_post_request.get('include_labels', False)
    include_labels = True if include_labels == 'yes' else False

    include_dates = data_post_request.get('include_dates', False)
    include_dates = True if include_dates == 'yes' else False

    single_sheet = data_post_request.get('single_sheet', False)
    single_sheet = True if single_sheet == 'yes' else False

    include_external_ids = data_post_request.get('include_external_ids', False)
    include_external_ids = True if include_external_ids == 'yes' else False


    # --------------------------------------------------------
    # get the file from the database
    manager = DataStructureHealthieDump()

    # some options here if needed
    manager.run_query(
        include_default_templates=False,
    )

    manager.include_labels = include_labels
    manager.include_dates = include_dates
    manager.single_sheet = single_sheet
    manager.include_external_ids = include_external_ids

    # get the data dump
    dump_bytes, full_name, mimetype, log = manager.get_data_dump(dump_data_type=dump_data_type)

    if dump_bytes is None or not log.get('success', False):
        abort(404)

    else:
        # Wrap the bytes data in an io.BytesIO object
        dump_file = io.BytesIO(dump_bytes)

        response = send_file(
            dump_file,
            as_attachment=True,
            download_name=full_name,
            mimetype=mimetype, # 'application/txt' or 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
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

