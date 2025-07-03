import os
import base64
import uuid
import boto3
import json
from typing import List, Tuple
from datetime import datetime, date, timedelta
import pytz
import pandas as pd

from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.api_healthie.conversations import HealthieConversations
from syntrillo.api_healthie.user import HealthieUser
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger
from syntrillo.system.tracer import tracer
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets
from syntrillo.api_tenovi.device_measurements import DeviceMeasurements

from constants import (
    AVERAGE_SYSTOLIC_BP_DAYS,
    AVERAGE_SYSTOLIC_BP_THRESHOLD,
    SYSTOLIC_BP_HIGH_THRESHOLD,
    SYSTOLIC_BP_LOW_THRESHOLD,
    AWS_SECRETS_MANAGER_HEALTHIE_IDS_SECRET_ARN_KEY,
    EXCLUDED_PATIENTS_KEY,
    MESSENGER_KEY,
    CLINICIANS_KEY
)

class BloodPressureAlertManager:
    """
    Handles blood pressure alert system.
    """

    def __init__(self, syntrillo_internal_key: str):
        lookup_manager = LookUpCodesManagement()
        entry = lookup_manager.retrieve_entry_by_internal_key(syntrillo_internal_key)

        self.syntrillo_internal_key = syntrillo_internal_key
        self.healthie_user_id = entry['healthie_user_id']


    def handle_single_measurement(self, event):
        payload = event
        # Check if the body is base64 (AWS API Gateway) encoded before decoding
        if payload.get('body', None) and self.is_base64(payload.get('body')):
            payload = self.decode_payload(payload.get('body', {}))

        # Extract patient_id and measurement data from Tenovi Webhook event
        patient_id = payload.get('patient_id', None)
        systolic_bp = float(payload.get('value_1', None))
        diastolic_bp = float(payload.get('value_2', None))
        timestamp = payload.get('timestamp', None)
        metric = payload.get('metric', None)

        if metric and metric != 'blood_pressure':
            logger.info(f"Pulse measurement received for patient {patient_id}")
            return {
                'statusCode': 200,
                'body': 'Tenovi pulse measurement received'
            }

        # Parse the UTC timestamp and convert to Eastern Time
        dt_utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        eastern = pytz.timezone("US/Eastern")
        dt_est = dt_utc.astimezone(eastern)

        # Format with EST included
        formatted_date = dt_est.strftime("%A (%-m/%-d/%y) at %-I:%M %p EST")

        logger.info(f"Current BP measurement for patient {patient_id} – systolic BP: {systolic_bp}, " +
                    f"diastolic BP: {diastolic_bp}, timestamp: {formatted_date}")

        # Get syntrillo_internal_key from the user_look_up_codes table using tenovi patient_id
        syntrillo_internal_key = self.get_syntrillo_internal_key_id_from_patient_id(patient_id)

        if not syntrillo_internal_key:
            logger.error(f"No syntrillo_internal_key found for tenovi_patient_id: {patient_id}")
            return {
                'statusCode': 400,
                'body': 'No syntrillo_internal_key found for tenovi_patient_id'
            }

        # 3. Check the systolic and diastolic BP values from Tenovi Webhook event to see if they are extreme and notify clinicians
        systolic_is_extreme = (
            systolic_bp is not None and
            (systolic_bp > SYSTOLIC_BP_HIGH_THRESHOLD or systolic_bp < SYSTOLIC_BP_LOW_THRESHOLD)
        )
        # diastolic_is_extreme = diastolic_bp > DIASTOLIC_BP_THRESHOLD if diastolic_bp is not None else False

        if systolic_is_extreme:
            # Send chat message notification to clinicians when extreme blood pressure is detected
            # self.notify_clinicians(syntrillo_internal_key, systolic_bp, diastolic_bp, formatted_date)
            body = "Alert sent thru Healthie."
        else:
            body = "No alert created."

        return {
            'statusCode': 200,
            'body': f'Successfully processed Tenovi Webhook Blood Pressure event. {body}'
        }

    def handle_2week_measurement(self):

        logger.info(f"Analyzing BP data for patient {self.syntrillo_internal_key}...")

        end_date = datetime.now(pytz.UTC)
        start_date = end_date - timedelta(weeks=4)
        mid_date = end_date - timedelta(weeks=2)

        db_manager = SyntrilloDatabaseManager(self.syntrillo_internal_key)

        df, log = db_manager.get_tenovi_device_metric_data(
            metric_name=DeviceMeasurements.TENOVI_METRICS_BPM_BLOOD_PRESSURE,
            start_date=start_date,
            end_date=end_date
        )

        # print(f"---- DATAFRAME -----: {df['value_1']}")

        if df is not None and not df.empty:
            # Convert timestamp_local to datetime if not already
            df['timestamp_local'] = pd.to_datetime(df['timestamp_local'])

            # Convert to UTC (assumes timestamp_local is timezone-aware or local time)
            if df['timestamp_local'].dt.tz is None:
                # If naive, localize to the correct local timezone first, e.g., 'America/New_York'
                df['timestamp_local'] = df['timestamp_local'].dt.tz_localize('America/New_York')
            # Convert to UTC
            df['timestamp_local'] = df['timestamp_local'].dt.tz_convert('UTC')

            # Now rename the column
            df = df.rename(columns={'timestamp_local': 'timestamp'})

            # Ensure the date column is datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Convert systolic ('value_1') values to numbers
            df['value_1'] = pd.to_numeric(df['value_1'], errors='coerce')

            # First two weeks: start_date <= timestamp < mid_date
            df_first = df[(df['timestamp'] >= start_date) & (df['timestamp'] < mid_date)]
            # Last two weeks: mid_date <= timestamp <= end_date
            df_last = df[(df['timestamp'] >= mid_date) & (df['timestamp'] <= end_date)]

            avg_first = round(df_first['value_1'].mean(), 1) if not df_first.empty and len(df_first) > 3 else None
            avg_last = round(df_last['value_1'].mean(), 1) if not df_last.empty and len(df_last) > 3 else None

            if avg_first is None or avg_last is None:
                logger.info(f"Insufficient data for patient {self.syntrillo_internal_key}: prior ({len(df_first)}); current ({len(df_last)})")
                return True

            if avg_last > avg_first:
                logger.info(f"Patient {self.syntrillo_internal_key} recorded a higher current 2-week average SBP ({avg_last}) than prior ({avg_first}). Sending notification...")
                content = f"<p></p><b>⚠️ PATIENT'S CURRENT 2-WEEK AVERAGE SBP EXCEEDS PRIOR 2-WEEK PERIOD.</b></p>\n<ul><li>Current: {df_last}</li>\n<li>Prior: {df_first}</li></ul>"
                return self.notify_clinicians(content)

        return

    # def notify_clinicians(self, syntrillo_internal_key: str, systolic_bp: float, diastolic_bp: float, timestamp: str) -> None:
    def notify_clinicians(self, content: str) -> None:
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
        user_manager = HealthieUser(self.healthie_user_id)
        patient_name = user_manager.get_name_by_healthie_user_id()

        # Retrieve healthie IDs env variable to use for conversation query
        secrets = LocalEnvironmentAndSecrets(load_healthie_secrets=True)
        healthie_ids = secrets.get_secrets(os.getenv(AWS_SECRETS_MANAGER_HEALTHIE_IDS_SECRET_ARN_KEY))

        # Check if the environment is production or staging to determine which clinicians to notify
        # Get environment from SSM parameter store to determine which clinicians to notify
        env = self.get_aws_environment()
        if not env:
            logger.error("Environment variable not found ...")
            return

        excluded_patients = healthie_ids.get(env, {}).get(EXCLUDED_PATIENTS_KEY, [])
        messenger_id = healthie_ids.get(env, {}).get(MESSENGER_KEY, "")
        clinicians = healthie_ids.get(env, {}).get(CLINICIANS_KEY, [])

        # If a specific patient is excluded from notifications, skip the notification
        if excluded_patients and self.healthie_user_id in excluded_patients:
            logger.info(f"Patient {patient_name} is excluded from notifications ...")
            return

        # The patient name is to be used as the title of the conversation
        # alert_title = f"⚠️ {patient_name} - BP Alert"
        alert_title = f"🔴 {patient_name} - BP Alert"

        conversation_manager = HealthieConversations()

        conversation_id = conversation_manager.get_conversation_by_title(alert_title, messenger_id)

        # Check if the conversation already exists
        # conversation_id = self.get_conversation_id(messenger_id, alert_title)

        if not conversation_id:
            # Create a new conversation
            conversation_output = self.make_conversation_query(clinicians, messenger_id, alert_title)
            conversation_id = conversation_output.get('createConversation', {}).get('conversation', {}).get('id')
            logger.info(f"Successfully created conversation in Healthie: {conversation_output}")

        # Add a note (aka a message) to the conversation
        # response = self.add_note_to_conversation(messenger_id, conversation_id, systolic_bp, diastolic_bp, timestamp, syntrillo_internal_key)

        message = conversation_manager.create_note(conversation_id=conversation_id, content=content, user_id=messenger_id)
        logger.info(f"Successfully added note to conversation in Healthie: {message}")


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

            logger.info(f"Clinicians str: {clinicians_str}")

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


if __name__ == '__main__':

    # patient_id = '1525423' # Patient AWS Test
    patient_id = '2315391' # Bob Barker

    lookup_manager = LookUpCodesManagement()

    entry = lookup_manager.retrieve_entry_by_healthie_user_id(patient_id)
    key = entry['syntrillo_internal_key']

    print(f"**** {key}")

    alert_manager = BloodPressureAlertManager(key)

    two_week_response = alert_manager.handle_2week_measurement()

    print(f"----- {two_week_response}")
