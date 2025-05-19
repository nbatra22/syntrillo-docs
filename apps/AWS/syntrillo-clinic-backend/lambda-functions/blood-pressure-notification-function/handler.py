import os
import base64
import uuid
import boto3
import json
from typing import List
from datetime import datetime, date, timedelta

from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger
from syntrillo.system.tracer import tracer
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets

from constants import (
    AVERAGE_SYSTOLIC_BP_DAYS,
    AVERAGE_SYSTOLIC_BP_THRESHOLD,
    SYSTOLIC_BP_THRESHOLD,
    DIASTOLIC_BP_THRESHOLD,
    HEALTHIE_BP_CONVERSATION_NAME,
    AWS_SECRETS_MANAGER_HEALTHIE_IDS_SECRET_ARN_KEY,
    EXCLUDED_PATIENTS_KEY,
    MESSENGER_KEY,
    CLINICIANS_KEY
)

# TODO: comment these decorators when running locally
# @tracer.capture_lambda_handler
# @logger.inject_lambda_context(log_event=True)
def handler(event, context):

    # Steps triggered by Tenovi webhooks:
    # 1. Extract patient_id and measurement data from event
    # 2. Push these measurements to MySQL database
    # 3. Validate systolic BP (value_1)
    # 4. Send notification to clinicians when extreme blood pressure (>170 || <90) is detected

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

    # {
    #     "metric": "string",
    #     "device_name": "string",
    #     "hwi_device_id": "string",
    #     "patient_id": "string",
    #     "hardware_uuid": "string",
    #     "sensor_code": "string",
    #     "value_1": "string",
    #     "value_2": "string",
    #     "created": "2019-08-24T14:16:18Z",
    #     "timestamp": "2019-08-24T14:15:22Z",
    #     "timezone_offset": -2147483648,
    #     "estimated_timestamp": false,
    #     "filter_params": {}
    # }

    # 1. Extract patient_id and measurement data from Tenovi Webhook event
    payload = event
    # Check if the body is base64 (AWS API Gateway) encoded before decoding
    if payload.get('body', None) and is_base64(payload.get('body')):
        payload = decode_payload(payload.get('body', {}))

    tenovi_patient_id = payload.get('patient_id', None)
    systolic_bp = float(payload.get('value_1', None))
    diastolic_bp = float(payload.get('value_2', None))
    timestamp = payload.get('timestamp', None)

    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    formatted_date = dt.strftime("%d %B %Y at %I:%M %p")

    logger.info(f"Current BP measurement for patient {tenovi_patient_id} – systolic BP: {systolic_bp}, " +
                f"diastolic BP: {diastolic_bp}, timestamp: {formatted_date}")

    # 2. Push these measurements to MySQL database
    # Get syntrillo_internal_key from the user_look_up_codes table using tenovi patient_id
    syntrillo_internal_key = get_syntrillo_internal_key_id_from_tenovi_patient_id(tenovi_patient_id)

    if not syntrillo_internal_key:
        logger.error(f"No syntrillo_internal_key found for tenovi_patient_id: {tenovi_patient_id}")
        return {
            'statusCode': 400,
            'body': 'No syntrillo_internal_key found for tenovi_patient_id'
        }

    # 4. Check the systolic and diastolic BP values from Tenovi Webhook event to see if they are extreme and notify clinicians
    systolic_is_extreme = systolic_bp > SYSTOLIC_BP_THRESHOLD if systolic_bp is not None else False
    diastolic_is_extreme = diastolic_bp < DIASTOLIC_BP_THRESHOLD if diastolic_bp is not None else False

    if systolic_is_extreme or diastolic_is_extreme:
        # Send chat messagenotification to clinicians when extreme blood pressure is detected
        notify_clinicians(syntrillo_internal_key, systolic_bp, diastolic_bp, formatted_date)


    return {
        'statusCode': 200,
        'body': 'Successfully processed Tenovi Webhook Blood Pressure event'
    }


def notify_clinicians(syntrillo_internal_key: str, systolic_bp: float, diastolic_bp: float, timestamp: str) -> None:
    """
    Notify clinicians when extreme blood pressure is detected

    Args:
        syntrillo_internal_key (str): Syntrillo internal key
        systolic_bp (float): Systolic blood pressure
        diastolic_bp (float): Diastolic blood pressure
        timestamp (str): Timestamp of the blood pressure measurement
    Returns:
        None
    """
    # Healthie Chat API Docs: https://docs.gethealthie.com/guides/chat/
    # Healthie Chat Overview: https://help.gethealthie.com/article/82-overview-chatting-with-a-client

    # 1. Create a new Healthie Conversation
    # Get patient name from the syntrillo_internal_key using the user_look_up_codes table
    patient_name, healthie_user_id = get_patient_name_from_syntrillo_internal_key(syntrillo_internal_key)

    # Retrieve healthie IDs env variable
    secrets = LocalEnvironmentAndSecrets(load_healthie_secrets=True)
    healthie_ids = secrets.get_secrets(os.getenv(AWS_SECRETS_MANAGER_HEALTHIE_IDS_SECRET_ARN_KEY))
    excluded_patients = healthie_ids.get(EXCLUDED_PATIENTS_KEY, None)

    # If a specific patient is excluded from notifications, skip the notification
    if excluded_patients and healthie_user_id in excluded_patients:
        logger.info(f"Patient {patient_name} is excluded from notifications ...")
        return

    # The patient name is to be used as the title of the conversation
    alert_title = HEALTHIE_BP_CONVERSATION_NAME + patient_name

    # Check if the environment is production or staging to determine which clinicians to notify
    # Get environment from SSM parameter store to determine which clinicians to notify
    env = get_aws_environment()
    if not env:
        logger.error("Environment variablenot found ...")
        return

    messenger_id = healthie_ids.get(env, {}).get(MESSENGER_KEY, None)
    clinicians = healthie_ids.get(env, {}).get(CLINICIANS_KEY, None)

    # Check if the conversation already exists
    conversation_id = get_conversation_id(messenger_id, alert_title)
    if not conversation_id:
        # Create a new conversation
        conversation_output = make_conversation_query(clinicians, messenger_id, alert_title)
        conversation_id = conversation_output.get('createConversation', {}).get('conversation', {}).get('id')
        logger.info(f"Successfully created conversation in Healthie: {conversation_output}")


    # Add a note (aka a message) to the conversation
    response = add_note_to_conversation(messenger_id, conversation_id, systolic_bp, diastolic_bp, timestamp, syntrillo_internal_key)
    logger.info(f"Successfully added note to conversation in Healthie: {response}")


def get_syntrillo_internal_key_id_from_tenovi_patient_id(tenovi_patient_id: str) -> str:

    """
    Single lookup of syntrillo_internal_key from the user_look_up_codes table using tenovi patient_id.

    Args:
        tenovi_patient_id (int): Tenovi patient ID from the Tenovi Webhook event
    Returns:
        dict: A dictionary mapping tenovi_patient_id to its corresponding syntrillo_internal_key
    """
    if not tenovi_patient_id:
        return None

    try:
        # Initialize the database manager specifically for the user_look_up_codes table
        db_manager = LookUpCodesManagement()
        db_connection = db_manager.conn

        # Create a cursor
        with db_connection.cursor() as cursor:

            # Query to retrieve syntrillo_internal_key from the user_look_up_codes table using tenovi patient_id
            select_query = """
                SELECT
                    BIN_TO_UUID(syntrillo_internal_key) as syntrillo_internal_key
                FROM user_look_up_codes
                WHERE BIN_TO_UUID(pseudo_code_for_tenovi_phi_access) = %s;
            """

            cursor.execute(select_query, (tenovi_patient_id,))
            entry = cursor.fetchone()

            # Return syntrillo internal key from the user_look_up_codes table
            if entry:
                logger.info(f"Successfully retrieved syntrillo_internal_key for tenovi_patient_id: {tenovi_patient_id}")
                return entry[0]
            else:
                logger.error(f"No entry found for tenovi_patient_id: {tenovi_patient_id}")
                return None

    except Exception as e:
        logger.error(f"Error retrieving syntrillo_internal_key from database: {e}")
        return None

    finally:
        db_connection.close()


def make_conversation_query(clinician_ids: List[str], messenger_id: str, alert_title: str) -> None:
    """
    Make a Healthie conversation query for the clinician

    Args:
        clinician_ids (List[str]): The ID of the clinician
        alert_title (str): The title of the alert
    Returns:
        None
    """
    graphql_query = '''
        mutation createConversation(
        $simple_added_users: String # e.g "user-1,group-2,user-3"
        $owner_id: ID # e.g "4"
        $name: String # e.g "Questions for Next Appointment"
        ) {
        createConversation(
            input: {
                simple_added_users: $simple_added_users,
                owner_id: $owner_id,
                name: $name
                }) {
            conversation {
                id
            }
            }
        }
    '''
    # Query output is dict with a single key called "data"
    # For example:
    #   {
    #         "createConversation": {
    #             "conversation": {
    #                 "id": "2720175"
    #             }
    #         }
    #   }

    logger.info("Creating conversation in Healthie")

    try:
        # Remove duplicates from the list of clinician IDs
        clinician_ids = list(set(clinician_ids))
        clinicians_str = f"{','.join(clinician_ids)}"

        variables = {
            "simple_added_users": clinicians_str,
            "owner_id": messenger_id,
            "name": alert_title
        }
        output: dict = HealthieUtils.run_graphql_query(graphql_query, variables)
        logger.info(f"Successfully created conversation in Healthie")

        return output

    except Exception as e:
        logger.error(f"Error creating conversation in Healthie: {e}")

def add_note_to_conversation(
        messenger_id: str,
        conversation_id: str,
        systolic_bp: float,
        diastolic_bp: float,
        timestamp: str,
        syntrillo_internal_key: str
) -> None:
    """
    Add a note to the conversation
    Args:
        messenger_id (str): The ID of the messenger
        conversation_id (str): The ID of the conversation
        systolic_bp (float): The systolic blood pressure
        diastolic_bp (float): The diastolic blood pressure
        timestamp (str): The timestamp of the blood pressure measurement
        syntrillo_internal_key (str): The Syntrillo internal key
    Returns:
        None
    """
    graphql_query = '''
        mutation createNote(
            $user_id: String
            $content: String
            $conversation_id: String
            ) {
            createNote(
                input: {
                user_id: $user_id
                content: $content # Content of the note
                conversation_id: $conversation_id
                }
            ) {
                note {
                id
                content
                user_id
                }
                messages {
                field
                message
                }
            }
        }
    '''
    # Query output is dict with a single key called "data"
    # For example:
    # {
    # "data": {
    #     "createNote": {
    #         "note": {
    #             "id": "364306", -- note id
    #             "content": "Try this", -- note content
    #                 "user_id": "1558940" -- user id
    #             }
    #         }
    #     }
    # }
    logger.info("Adding note to conversation in Healthie...")
    try:
        content = f"<ul><li>Time of measurement: {timestamp}</li> \n<li>Systolic BP: {systolic_bp}</li> \n<li>Diastolic BP: {diastolic_bp}</li></ul>"

        # Check if the patient has been experiencing extreme BP for a streak of days
        average_systolic_bp = get_average_systolic_bp_over_time_period(syntrillo_internal_key)
        # If the number of days extreme BP detected is -1, then there was an error retrieving the number of days
        if average_systolic_bp == -1:
            logger.warning(f"Could not retrieve average systolic BP over time period for {syntrillo_internal_key}")
        elif average_systolic_bp >= AVERAGE_SYSTOLIC_BP_THRESHOLD:
            content = f"<b>PATIENT HAS BEEN EXPERIENCING EXTREME BP FOR {AVERAGE_SYSTOLIC_BP_DAYS} DAYS. AVERAGE SYSTOLIC BP: {average_systolic_bp}</b>" + \
                "\n" + content

        variables = {
            "user_id": messenger_id,
            "content": content,
            "conversation_id": conversation_id
        }
        output: dict = HealthieUtils.run_graphql_query(graphql_query, variables)
        logger.info(f"Successfully created note in Healthie")

        return output

    except Exception as e:
        logger.error(f"Error adding note to conversation in Healthie: {e}")


def get_patient_name_from_syntrillo_internal_key(syntrillo_internal_key: str) -> tuple[str, str]:
    """
    Get patient name from the syntrillo_internal_key using the user_look_up_codes table
    Args:
        syntrillo_internal_key (str): The Syntrillo internal key
    Returns:
        tuple[str, str]: A tuple containing the patient name and healthie user id
    """

    # 1. Use syntrillo id to get healthie id
    db_manager = LookUpCodesManagement()
    entry = db_manager.retrieve_entry_by_internal_key(syntrillo_internal_key)
    healthie_user_id = entry.get('healthie_user_id', None)
    if not healthie_user_id:
        logger.error(f"Healthie user id not found for syntrillo_internal_key: {syntrillo_internal_key}")
        return

    # 2. Use healthie id to get patient name from Healthie API
    patient_name = get_healthie_user_information_by_healthie_user_id(healthie_user_id)
    if not patient_name:
        logger.error(f"Patient name not found for syntrillo_internal_key: {syntrillo_internal_key}")
        return
    return patient_name, healthie_user_id


def get_healthie_user_information_by_healthie_user_id(healthie_user_id: str) -> str:
    """
    Get patient name from the healthie user id using the Healthie API
    Args:
        healthie_user_id (str): The ID of the healthie user
    Returns:
        str: The patient name
    """
    graphql_query = '''
        query getUser($id: ID) {
            user(id: $id) {
            id
            first_name
            last_name
            }
        }
    '''
    # Query output is dict with a single key called "data"
    # For example:
    # {
    #     "data": {
    #         "user": {
    #             "id": "2315391",
    #             "first_name": "Bob",
    #             "last_name": "Barker",
    #         }
    #     }
    # }
    logger.info("Adding note to conversation in Healthie...")
    try:
        variables = {
            "id": healthie_user_id
        }
        output: dict = HealthieUtils.run_graphql_query(graphql_query, variables)
        logger.info(f"Successfully retrieved user information from Healthie")

        first_name = output.get('user', {}).get('first_name', '')
        last_name = output.get('user', {}).get('last_name', '')
        return first_name + " " + last_name

    except Exception as e:
        logger.error(f"Error fetching user information from Healthie: {e}")


def get_aws_environment() -> str:
    """
    Get the environment from the SSM parameter store
    Args:
        None
    Returns:
        str: The environment
    """
    # Initialize AWS Systems Manager (SSM) client
    logger.info("Retrieving environment variable from AWS...")
    try:
        AWS_ENVIRONMENT = os.environ['AWS_ENVIRONMENT']
        logger.info(f"Environment: {AWS_ENVIRONMENT}")
        return AWS_ENVIRONMENT
    except Exception as e:
        logger.error(f"Error retrieving environment variable from AWS: {e}")
        return None

def get_aws_clinician_ids() -> List[str]:
    """
    Get the environment from the SSM parameter store
    Args:
        None
    Returns:
        str: The environment
    """
    # Initialize AWS Systems Manager (SSM) client
    logger.info("Retrieving env specific clinician ids from AWS...")
    try:
        AWS_CLINICIAN_IDS = os.environ['CLINICIAN_IDS']
        return AWS_CLINICIAN_IDS
    except Exception as e:
        logger.error(f"Error retrieving environment variable from AWS: {e}")
        return None


def get_conversation_id(messenger_id: str, alert_title: str) -> str:
    """
    Get the conversation id from the Healthie API
    Args:
        messenger_id (str): The ID of the messenger
        alert_title (str): The title of the alert
    Returns:
        str: The conversation id
    """
    graphql_query = '''
        query conversationMemberships(
        $keywords: String
        $provider_id: ID
        ) {
        conversationMembershipsCount(
            keywords: $keywords
            provider_id: $provider_id

        )
        conversationMemberships(
            keywords: $keywords
            provider_id: $provider_id
        ) {
            id
            display_name
            convo {
            id
            conversation_memberships_count
            }
        }
    }
    '''
    '''
    Example output:
    {
        "data": {
            "conversationMembershipsCount": 1,
            "conversationMemberships": [
                {
                    "id": "15583438",
                    "display_name": "Multiple_users_01",
                    "archived": false,
                    "viewed": true,
                    "convo": {
                        "id": "2776123",
                        "conversation_memberships_count": 3
                    }
                }
            ]
        }
    }
    '''
    try:
        variables = {
            "keywords": alert_title,
            "provider_id": messenger_id
        }
        output: dict = HealthieUtils.run_graphql_query(graphql_query, variables)
        logger.info(f"Successfully retrieved conversation memberships from Healthie")

        conversation_id = output.get('conversationMemberships', {})[0].get('convo', {}).get('id', None)
        return conversation_id

    except Exception as e:
        logger.error(f"Error fetching conversation id from Healthie: {e}")
        return None

def get_average_systolic_bp_over_time_period(syntrillo_internal_key: str) -> float:
    """
    Get the average systolic BP over a time period for a patient
    Args:
        syntrillo_internal_key (str): The Syntrillo internal key
    Returns:
        float: The average systolic BP
    """
    # BP API Docs: https://api2.tenovi.com/hwi-redoc/#tag/hwi-patient-measurements
    db_manager = SyntrilloDatabaseManager(syntrillo_internal_key=syntrillo_internal_key)
    average_systolic_bp, log = db_manager.get_average_systolic_bp_over_time_period(
        number_of_days=AVERAGE_SYSTOLIC_BP_DAYS
    )

    if not log.get('success', False) or not average_systolic_bp:
        logger.warning(f"Could not retrieve average systolic BP over time period for {syntrillo_internal_key}. Log: {log}")
        return -1

    return average_systolic_bp

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
