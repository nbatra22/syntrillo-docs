import base64
import json

from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger
from syntrillo.system.tracer import tracer
from syntrillo.bp_alerts.bp_alert_manager import BloodPressureAlertManager

# TODO: comment these decorators when running locally
@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, context):

    # Event format:
    # {
    #   "metric": "pulse",
    #   "device_name": "Tenovi BPM",
    #   "hwi_device_id": "12345678-abcd-1234-abcd-1234567890ab",
    #   "patient_id": "54321",
    #   "hardware_uuid": "1234ABCD5678",
    #   "sensor_code": "10",
    #   "value_1": "100.00",
    #   "value_2": "0.00",
    #   "created": "2025-01-16T17:34:47.025219Z",
    #   "timestamp": "2025-01-16T17:34:47.025219Z",
    #   "timezone_offset": 0,
    #   "estimated_timestamp": false,
    #   "filter_params": null
    # }

    payload = event

    # Check if the body is base64 (AWS API Gateway) encoded before decoding
    if payload.get('body', None) and is_base64(payload.get('body')):
        payload = decode_payload(payload.get('body', {}))

    patient_id = payload.get('patient_id', None)

    if not patient_id:
        raise ValueError(f"No patient_id provided")

    lookup_codes = LookUpCodesManagement()
    entry = lookup_codes.retrieve_entry_by_healthie_user_id(patient_id)
    syntrillo_internal_key = entry['syntrillo_internal_key']

    alert_manager = BloodPressureAlertManager(syntrillo_internal_key, patient_id, calculate_timeframed_data=False)

    return alert_manager.handle_single_measurement(payload)

def is_base64(body: str) -> bool:
    """
    Check if a string is base64 encoded

    Args:
        s (str): String to check
    Returns:
        bool: True if the string is base64 encoded, False otherwise
    """
    if not isinstance(body, str):
        return False

    try:
        # Check if string has valid base64 characters
        if not all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in body):
            return False

        # Try to decode
        decoded = base64.b64decode(body)
        # Try to parse as JSON to ensure it's a valid payload
        json.loads(decoded)
        return True
    except (ValueError, TypeError, json.JSONDecodeError):
        return False

def decode_payload(base64_str: str) -> dict:
    """
    Decode a Base64 string back to a JSON payload
    Args:
        base64_str (str): The Base64 string to decode
    Returns:
        dict: The decoded JSON payload
    """
    # Decode the Base64 string to bytes
    json_bytes = base64.b64decode(base64_str)

    # Decode the bytes to a JSON string
    json_str = json_bytes.decode('utf-8')

    # Parse the JSON string to a dictionary
    payload = json.loads(json_str)

    return payload
