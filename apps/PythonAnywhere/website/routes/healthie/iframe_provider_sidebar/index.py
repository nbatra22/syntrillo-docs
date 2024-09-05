# Path: ./apps/PythonAnywhere/website/routes/healthie/iframe_provider_sidebar/index.py

from flask import Blueprint, request, render_template, abort
import os

from syntrillo.system.iframe_validator import IframeValidator
from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets


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
        abort(403, description="Access Denied")

    # --------------------------------------------------------------------
    # load secrets and environment variables to retrieve local environment specific tweaks used mainly for debugging
    secrets = LocalEnvironmentAndSecrets(load_healthie_secrets=True)

    # --------------------------------------------------------------------
    # Retrieve the JSON data from the GET request
    data_get_request = request.args.to_dict()

    # Extract hl_current_user_id from data_get_request
    # here it is the provider id
    healthie_provider_id = data_get_request.get('hl_current_user_id')

    if healthie_provider_id is None:
        healthie_provider_id = "1033222" # "-1"

    # --------------------------------------------------------------------
    # milliseconds_delay

    if secrets.is_lambda and secrets.is_staging:
        # if running on AWS Lambda and in staging environment use a longer delay to allow lambdas to initialize
        milliseconds_delay_default = 5000
    else:
        milliseconds_delay_default = 1000

    # if os env variable MILLISECONDS_DELAY exists use it else use default
    #   : useful locally since some delay needed to prevent a server error on VSCode Live Server
    milliseconds_delay = int( os.getenv('MILLISECONDS_DELAY', milliseconds_delay_default) )

    return render_template('healthie/iframe_provider_sidebar/index.html',
                           healthie_provider_id=healthie_provider_id,
                           iframe_log=iframe_log,
                           milliseconds_delay=milliseconds_delay
                           )