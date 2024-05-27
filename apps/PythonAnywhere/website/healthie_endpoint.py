# Path: ./apps/PythonAnywhere/website/healthie_endpoint.py

"""

routes to healthy webhooks endpoints

"""

from flask import Blueprint, request, jsonify, render_template
import json

# ----- healthie package integration --------------

# python anywhere requirements
#    pip install python-dotenv

# python.analysis.extraPaths added into .vscode/settings.json
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.api_healthie.misc import log_this
from syntrillo.virtual_care_navigator.virtual_care_navigator import VirtualCareNavigator

# -------------------------------------------------

healthie_endpoint_bp = Blueprint('healthie_endpoint', __name__)

# whitelisting Healthie's IP addresses : Healthie does not sign its webhook events. https://docs.gethealthie.com/docs/#webhooks
# Define the whitelist of allowed IP addresses
ALLOWED_IPS = ['192.168.0.1', '10.0.0.1', '127.0.0.1',  # local IPs
               '18.206.70.225', '44.195.8.253',         # staging
               '52.4.158.130', '3.216.152.234',         # production
               ]


@healthie_endpoint_bp.route('/healthie_endpoint_post', methods=['POST'])
def healthie_endpoint_post():
    """
    This is the single endpoint of healthie webhooks.

    See https://docs.gethealthie.com/docs/#webhooks

        "resource_id": resource_id, # The ID of the resource that was affected
        "resource_id_type": resource_id_type, # The type of resource (can be 'Appointment', 'FormAnswerGroup', 'Entry', or 'Note')
        "event_type": event_type # The event that occurred

    """

    # Get the IP address of the incoming request
    # remote_ip = request.remote_addr # returns a private address on PA : '10.0.0.20'
    # log_this(remote_ip)
    remote_ip = request.headers.get('X-Real-IP', request.remote_addr)
    log_this(remote_ip)

    # Check if the remote IP is in the whitelist
    if remote_ip not in ALLOWED_IPS:
        message = {'error': f'Unauthorized access. Your IP is not whitelisted. {remote_ip}'}
        log_this(message=message)
        return jsonify(message), 401

    # Retrieve the JSON data from the POST request
    data = request.json

    # Log the data to a local file
    with open('ignore_healthie_endpoint_post_logs.txt', 'a') as f:
        f.write(json.dumps(data) + '\n\n')

    # Load environment variables from .env file
    dotenv_path = ".env"

    # Dispatch
    # {"resource_id": 260040, "resource_id_type": "Note", "event_type": "message.created", "changed_fields": []}
    if data['resource_id_type'] == "Note":
        log_this(message="VCN endpoint")
        vcn = VirtualCareNavigator(dotenv_path=dotenv_path)
        vcn.endpoint(data=data)


    return jsonify({'message': 'Webhook received'}), 200


@healthie_endpoint_bp.route('/healthie_endpoint_get', methods=['GET'])
def healthie_endpoint_get():
    # log the post request in a local file for testing

    # Retrieve the JSON data from the GET request
    data = request.args.to_dict()

    # Log the data to a local file
    with open('ignore_webhook_get_logs.txt', 'a') as f:
        f.write(json.dumps(data) + '\n\n')

    return jsonify({'message': 'Webhook received'}), 200


@healthie_endpoint_bp.route('/healthie_test_org', methods=['GET'])
def healthie_test_org() :
    """
    Tests connection with Healthie API

    Returns organization details as JSON
    """
    # Load environment variables from .env file
    dotenv_path = ".env"

    try:
        # Create an instance of HealthieAPI with the provided API key and organization
        utils_api = HealthieUtils(dotenv_path=dotenv_path)

        # Example: Get organization details
        organization_details = utils_api.get_organization_details()

        return jsonify({'organization_details': organization_details}), 200

    except Exception as e:
        # Construct detailed error response
        error_details = {
            'message': str(e),  # Get string representation of the exception
            'dotenv_path': dotenv_path
        }

        # Return JSON response with error details and appropriate HTTP status code (e.g., 500 for internal server error)
        return jsonify({'error': error_details}), 500

