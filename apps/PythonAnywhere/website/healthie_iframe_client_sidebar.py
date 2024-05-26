# Path: ./apps/PythonAnywhere/website/healthie_iframe_client_sidebar.py

"""

route to iframe_healthie_client_sidebar and related actions

"""

from flask import Blueprint, request, jsonify, render_template
import json

import os
import sys

# ----- healthie package integration --------------

# python anywhere requirements
#    pip install python-dotenv

# python.analysis.extraPaths added into .vscode/settings.json
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.api_healthie.misc import extract_user_id_from_url
from syntrillo.api_healthie.forms import HealthieForms

from syntrillo.data_structures.data_structure import DataStructure
from syntrillo.data_structures.storage_manager import StorageManager

# -------------------------------------------------

healthie_iframe_client_sidebar_bp = Blueprint('healthie_iframe_client_sidebar', __name__)


# =============================================================================================================
# CLIENT SIDE BAR IFRAME

@healthie_iframe_client_sidebar_bp.route('/iframe_healthie_client_sidebar', methods=['GET'])
def iframe_healthie_client_sidebar():
    """
    iframe displayed in :

    Client portal, extra sidebar item:
        hl_current_user_id: 1035117 # that's the patient ID
        referrer_url: https://securestaging.gethealthie.com/

    """

    # --------------------------------------------------------------------
    # Retrieve the JSON data from the GET request
    data_get_request = request.args.to_dict()

    # Log the data to a local file
    with open('ignore_healthy_iframes_logs.txt', 'a') as f:
        f.write(json.dumps(data_get_request) + '\n\n')

    # Extract hl_current_user_id from data_get_request
    # here, it's the patient_id
    patient_id = data_get_request.get('hl_current_user_id')

    # --------------------------------------------------------------------

    # Render the 'healthie_client_sidebar.html' template with the provided data
    return render_template('healthie_client_sidebar.html',
                           data_get_request=data_get_request,
                           patient_id=patient_id
                           )


# =============================================================================================================
# BUTTONS IN CLIENT SIDEBAR IFRAME
