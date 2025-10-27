# Path: ./apps/PythonAnywhere/website/routes/healthie/endpoints.py

"""
routes to healthie webhooks endpoints
"""
# ----- healthie package integration --------------
# python anywhere requirements
#    pip install python-dotenv

from flask import Blueprint, request, jsonify
import json
from datetime import datetime

# python.analysis.extraPaths added into .vscode/settings.json
from syntrillo.system.logger import logger
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.chatbots.dispatcher import ChatBotsDispatcher
from syntrillo.patient_initialization.new_patient_created import NewPatientCreated
from syntrillo.remote_monitoring.syntrillo_medications_db_manager import SyntrilloMedicationsDatabaseQueries
from syntrillo.medications.utils import process_medication_webhook_event


healthie_endpoint_bp = Blueprint('healthie_endpoint', __name__)

# Whitelisting Healthie's IP addresses : Healthie does not sign its webhook events. https://docs.gethealthie.com/docs/#webhooks
# Define the whitelist of allowed IP addresses
ALLOWED_IPS = [
    '192.168.0.1', '10.0.0.1', '127.0.0.1',                            # local IPs
    '18.206.70.225', '44.195.8.253',                                   # staging
    '52.4.158.130', '3.216.152.234', '54.243.233.84', '50.19.211.21',  # production
]

@healthie_endpoint_bp.route('/healthie_endpoint_post', methods=['POST'])
def healthie_endpoint_post():
    """
    This is the single endpoint of healthie webhooks.

    https://api.staging.syntrillo-clinic-backend.com/healthie_endpoint_post

    See https://docs.gethealthie.com/docs/#webhooks

    {
        "resource_id": resource_id, # The ID of the resource that was affected
        "resource_id_type": resource_id_type, # The type of resource (can be 'Appointment', 'FormAnswerGroup', 'Entry', or 'Note')
        "event_type": event_type # The event that occurred
    }
    """

    # Get the IP address of the incoming request
    # remote_ip = request.remote_addr # returns a private address on PA : '10.0.0.20'
    remote_ip = request.headers.get('X-Real-IP', request.remote_addr)

    # Check if the remote IP is in the whitelist
    if remote_ip not in ALLOWED_IPS:
        message = {'error': f'Unauthorized access. Your IP is not whitelisted. {remote_ip}'}
        return jsonify(message), 401

    # Retrieve the JSON data from the POST request
    data = request.json
    if not data:
        logger.error("Invalid webhook payload: %r", data)
        return {"error": "Invalid payload"}, 400

    # TODO : Log the data json.dumps(data)

    logger.info(f"Endpoint : start post: {datetime.now()}")

    # Message created in the chat. The webhook fires when a message is sent in the chat.
    #   {"resource_id": 260040, "resource_id_type": "Note", "event_type": "message.created", "changed_fields": []}
    if data['resource_id_type'] == "Note" and data['event_type'] == "message.created":
        # TODO log (message="Endpoint : Note : message.created")
        logger.info("Endpoint : Note : message.created")
        start_time = datetime.now()
        chatbot = ChatBotsDispatcher()
        chatbot.endpoint(data=data)
        duration = (datetime.now() - start_time).total_seconds()
        logger.info({
            "message": "> Time to execute chatbot endpoint",
            "duration_seconds": duration
        })

    # Patient created on the provider 'Add Client' page. The webhook fires before the patient logs in for the first time.
    #   {"resource_id": 1209676, "resource_id_type": "User", "event_type": "patient.created", "changed_fields": []}
    elif data['resource_id_type'] == "User" and data['event_type'] == "patient.created":
        # TODO : log (message="Endpoint : User : patient.created")
        logger.info("Endpoint : User : patient.created")
        npc = NewPatientCreated()
        npc.endpoint(data=data)

    # Example payload: {"resource_id":58612,"resource_id_type":"Medication","event_type":"medication.updated","changed_fields":["dosage","start_date"],"user_id":1562903}
    elif data['resource_id_type'] == "Medication":

        # Get Healthie user id from payload ("user_id")
        healthie_user_id = str(data.get("user_id"))
        medication_id = str(data.get("resource_id"))
        event_type = data["event_type"]

        if event_type in ["medication.create", "medication.update"]:
            logger.info(f"Healthie {event_type} medications webhook event triggered...")
            # Process the webhook event for medication.create, medication.update, medication.delete
            process_medication_webhook_event(healthie_user_id, medication_id, event_type)

        else:
            # This means the record was medication.delete so we delete all records from our DB
            logger.info(f"Deleting medication with medication_id: {medication_id}")
            db_medication_manager = SyntrilloMedicationsDatabaseQueries()
            db_medication_manager.delete_medication_records(medication_id)
            logger.info("Successfully deleted medication...")

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

    try:
        # Create an instance of HealthieAPI with the provided API key and organization
        utils_api = HealthieUtils()

        # Example: Get organization details
        organization_details = utils_api.get_organization_details()

        return jsonify({'organization_details': organization_details}), 200

    except Exception as e:
        # Construct detailed error response
        error_details = {
            'message': str(e),  # Get string representation of the exception
            'type': type(e).__name__,  # Get the name of the exception class
        }

        # Return JSON response with error details and appropriate HTTP status code (e.g., 500 for internal server error)
        return jsonify({'error': error_details}), 500

