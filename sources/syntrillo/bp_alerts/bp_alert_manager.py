
from typing import List
from datetime import datetime, timedelta
import pytz
import pandas as pd
import uuid

from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.api_healthie.conversations import HealthieConversations
from syntrillo.api_healthie.user import HealthieUser
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets
from syntrillo.api_tenovi.device_measurements import DeviceMeasurements
from syntrillo.bp_analysis.bp_analysis import BloodPressureAnalysis

from syntrillo.bp_alerts.constants import (
    SYSTOLIC_BP_HIGH_THRESHOLD,
    SYSTOLIC_BP_LOW_THRESHOLD,
)

class BloodPressureAlertManager:
    """
    Handles blood pressure alert system.
    """

    def __init__(self, syntrillo_internal_key: str, healthie_user_id: str):
        self.syntrillo_internal_key = syntrillo_internal_key
        self.healthie_user_id = healthie_user_id


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
            self.notify_clinicians(syntrillo_internal_key, systolic_bp, diastolic_bp, formatted_date)
            body = "Alert sent thru Healthie."
        else:
            body = "No alert created."

        return {
            'statusCode': 200,
            'body': f'Successfully processed Tenovi Webhook Blood Pressure event. {body}'
        }

    def handle_two_week_measurement(self) -> None:
        """
        Analyze specific patient's BP data over the last 4 weeks (2 weeks prior and 2 weeks after)
        and determine if to notify clinicians.

        Args:
            None
        Returns:
            None
        Raises:
            e (Exception): General exception from retrieving the BP data from the database
        """
        logger.info(f"Analyzing BP data for patient {self.syntrillo_internal_key}...")

        try:
            end_date = datetime.now(pytz.UTC)
            start_date = end_date - timedelta(weeks=4)
            mid_date = end_date - timedelta(weeks=2)

            db_manager = SyntrilloDatabaseManager(self.syntrillo_internal_key)

            df, log = db_manager.get_tenovi_device_metric_data(
                metric_name=DeviceMeasurements.TENOVI_METRICS_BPM_BLOOD_PRESSURE,
                start_date=start_date,
                end_date=end_date
            )

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

                # Prior 2-week period: start_date <= timestamp < mid_date
                prior_period_condition = (df['timestamp'] >= start_date) & (df['timestamp'] < mid_date)
                df_prior = df[prior_period_condition]

                # Current 2-week period: mid_date <= timestamp <= end_date
                current_period_condition = (df['timestamp'] >= mid_date) & (df['timestamp'] <= end_date)
                df_current = df[current_period_condition]

                avg_prior = round(df_prior['value_1'].mean(), 1) if not df_prior.empty and len(df_prior) > 3 else None
                avg_current = round(df_current['value_1'].mean(), 1) if not df_current.empty and len(df_current) > 3 else None

                if avg_prior is None or avg_current is None:
                    logger.info(f"Insufficient data for patient {self.syntrillo_internal_key}: prior ({len(df_prior)}); current ({len(df_current)})")
                    return

                if avg_current > avg_prior:
                    logger.info(f"Patient {self.syntrillo_internal_key} recorded a higher current 2-week average SBP ({avg_current}) than prior ({avg_prior}). Sending notification...")
                    content = (
                        f"<p></p><b>⚠️ PATIENT'S CURRENT 2-WEEK AVERAGE SBP EXCEEDS PRIOR 2-WEEK AVERAGE.</b></p>\n"
                        f"<ul><li>Current ({mid_date.strftime('%-m/%-d/%y')} – {end_date.strftime('%-m/%-d/%y')}): {avg_current}</li>\n"
                        f"<li>Prior ({start_date.strftime('%-m/%-d/%y')} – {(mid_date - timedelta(days=1)).strftime('%-m/%-d/%y')}): {avg_prior}</li></ul>"
                    )
                    self.notify_clinicians(content)

            return None

        except Exception as e:
            logger.error(f"Error analyzing BP data for patient {self.syntrillo_internal_key}: {e}")
            raise e


    def handle_two_week_status(self) -> None:
        """
        Checks for decrease in patients overall status (using BloodPressureAnalysis class) and notifies clinicians if so.

        """
        logger.info(f"Analyzing patient {self.syntrillo_internal_key} overall categorization...")

        status_points = {
            'Poor': 0,
            'Okay': 1,
            'Good': 2
        }

        try:
            bp_analysis = BloodPressureAnalysis(self.syntrillo_internal_key)

            end_date = datetime.today()
            start_date = datetime.today() - pd.Timedelta(weeks=1, days=1)


            _, log = bp_analysis.get_blood_pressure_dataframe(
                start_date=None,
                end_date=None
            )

            if log['success'] == False:
                logger.error(f"Error fetching BP data: {log['error']}")

            if _.empty:
                logger.info(f"Insufficient BP data for patient {self.syntrillo_internal_key}")
                return

            timeframes = bp_analysis.calculate_timeframes()
            analysis_df = bp_analysis.calculate_analysis()

            if 'Latest' in analysis_df.columns:
                logger.info(f"Patient {self.syntrillo_internal_key} does not have recent measurements")
                print(f"{analysis_df}")
                return "Bye"

            current_status = analysis_df['Current']['Overall']
            prior_status = analysis_df['Prior']['Overall']

            current_pts = status_points[current_status]
            prior_pts = status_points[prior_status]

            if current_pts < prior_pts:
                content = f"<b>⚠️ PATIENT'S OVERALL STATUS CHANGED FROM '{prior_status}' TO '{current_status}'.</b>"
                # print(f"Current: {current_status} // Prior: {prior_status}")
                # content = f""
                self.notify_clinicians(content)
                print(f"Notification sent for patient {self.syntrillo_internal_key}. Overall status changed from {prior_status} to {current_status}.")
                logger.info(f"Notification sent for patient {self.syntrillo_internal_key}. Overall status changed from {prior_status} to {current_status}.")
            else:
                print(f"No notification sent for patient {self.syntrillo_internal_key}. No overall status change detected.")
                logger.info(f"No notification sent for patient {self.syntrillo_internal_key}. No overall status change detected.")

        except Exception as e:
            logger.error(f"Error analyzing overall status for patient {self.syntrillo_internal_key}: {e}")
            raise e

        return


    def notify_clinicians(self, content: str) -> None:
        """
        Notify clinicians when extreme blood pressure is detected

        Args:
            content (str): Content of the notification to be passed into the create_note mutation.
        Returns:
            None
        Raises:
            Exception: If there is an error creating the conversation in Healthie
        """
        # Healthie Chat API Docs: https://docs.gethealthie.com/guides/chat/
        # Healthie Chat Overview: https://help.gethealthie.com/article/82-overview-chatting-with-a-client

        # 1. Create a new Healthie Conversation
        # Get patient name from the syntrillo_internal_key using the user_look_up_codes table
        try:
            user_manager = HealthieUser(self.healthie_user_id)
            patient_name = user_manager.get_name_by_healthie_user_id()

            # Retrieve healthie IDs env variable to use for conversation query
            secrets = LocalEnvironmentAndSecrets(load_healthie_ids_secrets=True)

            excluded_patients = secrets.get_secret_value('healthie_ids', 'excluded_patients')
            messenger_id = secrets.get_secret_value('healthie_ids', 'messenger_id')
            clinicians = secrets.get_secret_value('healthie_ids', 'clinicians')

            # If a specific patient is excluded from notifications, skip the notification
            if excluded_patients and self.healthie_user_id in excluded_patients:
                logger.info(f"Patient {patient_name} is excluded from notifications ...")
                return

            # The patient name is to be used as the title of the conversation
            # alert_title = f"⚠️ {patient_name} - BP Alert"
            alert_title = f"🔴 {patient_name} - BP Alert"

            conversation_manager = HealthieConversations()

            conversation_id = conversation_manager.get_conversation_by_title(alert_title, messenger_id)
            if not conversation_id:
                # Create a new conversation
                conversation_output = self.make_conversation_query(clinicians, messenger_id, alert_title)
                if not conversation_output:
                    raise Exception(f"Error creating conversation in Healthie")

                conversation_id = conversation_output.get('createConversation', {}).get('conversation', {}).get('id')
                logger.info(f"Successfully created conversation in Healthie: {conversation_output}")

            # Add a note (aka a message) to the conversation
            # response = self.add_note_to_conversation(messenger_id, conversation_id, systolic_bp, diastolic_bp, timestamp, syntrillo_internal_key)

            message = conversation_manager.create_note(conversation_id=conversation_id, content=content, user_id=messenger_id)
            logger.info(f"Successfully added note to conversation in Healthie: {message}")

        except Exception as e:
            logger.error(f"Error notifying clinicians: {e}")
            raise e


    def make_conversation_query(self, clinician_ids: List[str], messenger_id: str, alert_title: str) -> None:
        """
        Make a Healthie conversation query for the clinician

        Args:
            clinician_ids (List[str]): The ID of the clinician
            messenger_id (str): The ID of the messenger
            alert_title (str): The name of the patient
        Returns:
            None
        Raises:
            e (Exception): General exception from creating the conversation in Healthie
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
            # Convert the clinician_ids to a GraphQL valid variable string
            if type(clinician_ids) is list:
                # If the clinician_ids is a list, remove duplicates and convert to a string
                clinician_ids = list(set(clinician_ids))
                clinician_ids = f"{','.join(clinician_ids)}"

            logger.info(f"Clinicians str: {clinician_ids}")

            variables = {
                "simple_added_users": clinician_ids,
                "owner_id": messenger_id,
                "name": alert_title
            }
            output: dict = HealthieUtils.run_graphql_query(graphql_query, variables)
            logger.info(f"Successfully created conversation in Healthie")

            return output

        except Exception as e:
            logger.error(f"Error creating conversation in Healthie: {e}")



if __name__ == '__main__':

    # patient_id = '1525423' # Patient AWS Test
    patient_id = '1966294' # Patient AWS Test 3
    # patient_id = '2315391' # Bob Barker

    lookup_manager = LookUpCodesManagement()

    entry = lookup_manager.retrieve_entry_by_healthie_user_id(patient_id)
    key = entry['syntrillo_internal_key']

    print(f"**** {key}")

    alert_manager = BloodPressureAlertManager(key, patient_id)

    # two_week_measurement_response = alert_manager.handle_two_week_measurement()

    # print(f"----- {two_week_measurement_response}")

    two_week_status_response = alert_manager.handle_two_week_status()
