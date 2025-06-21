from flask import jsonify
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.billing.models import BillingEligibility
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.billing.candid_manager import CandidHealthManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger
from datetime import timedelta
from syntrillo.billing.constants import CPT_CODE, DEVICE_TRAINING_FORM_NAME
from syntrillo.api_healthie.user import HealthieUser
import uuid
import json


class BillingManager:
    """
    This class is used to manage the billing of the patients.
    """
    def __init__(self):
        self.db_manager = SyntrilloDatabaseManager(syntrillo_internal_key="NOT_USED")
        self.lookup_codes_manager = LookUpCodesManagement()
        self.candid_manager = CandidHealthManager()

        self.cpt_bp_code = CPT_CODE


    def sync_billing_eligibility_data(self) -> None:
        """
        Retrieve billing eligibility data from Healthie and insert into internal AWS RDS DB

        Args:
            None
        Returns:
            None
        Raises:
            e (Exception): General exception when retrieve billing eligibility data from Healthie and insert into internal AWS RDS DB
        """
        try:
            # Get all healthie patients
            all_patient_data = self.get_healthie_patient_data()
            if not all_patient_data:
                logger.warning("Error: No patient information returned from Healthie")
                return { "all_patient_data": []}

            # Loop through list of patients and get Billing Eligibility data
            all_patient_billing_eligibility = []
            for patient in all_patient_data:

                healthie_user_id = patient.get('id', None)
                syntrillo_internal_key_response = self.lookup_codes_manager.retrieve_entry_by_healthie_user_id(healthie_user_id)

                # If, for some reason, a healthie ID does not have a syntrillo_internal_key, don't incorporate them.
                if not syntrillo_internal_key_response:
                    logger.warning(f"Patient {patient} does not have a healthie user id")
                    continue
                syntrillo_internal_key = syntrillo_internal_key_response['syntrillo_internal_key']

                # Get BP device training status (A form from healthie)
                bp_device_training_status = self.get_bp_device_training_status(healthie_user_id)

                # Get BP the dates with at least 1 BP measurement
                bp_data, _ = self.db_manager.get_all_patient_bp_data_by_syntrillo_internal_key(syntrillo_internal_key)

                # Get billing information for the patient
                billing_information = self.candid_manager.get_patient_billing_data(syntrillo_internal_key)

                # Check if the patient is eligible for billing
                eligible_for_billing = self.is_patient_eligible_for_billing(bp_data, bp_device_training_status, billing_information)

                # Create a billing eligibility object
                billing_eligibility = BillingEligibility(
                    syntrillo_internal_key=str(syntrillo_internal_key),
                    cpt_code=self.cpt_bp_code,
                    bp_device_training_status=bp_device_training_status,
                    eligible_to_bill=eligible_for_billing
                )

                all_patient_billing_eligibility.append(billing_eligibility)

            # Insert the billing eligibility data into the database
            self.insert_billing_eligibility_data(all_patient_billing_eligibility)

        except Exception as e:
            logger.error(f"Error while syncing billing eligibility data: {e}")
            raise e

    def get_all_patient_eligibility_data(self) -> list[dict]:
        """
        Gets all patient eligibility data from AWS RDS billing_eligibility table

        Args:
            None
        Returns:
            list[dict]: List of patient data
        """
        all_patient_eligibility_data = self.retrieve_patient_eligibility_data()

        all_patient_data = []

        for patient_eligibility_data in all_patient_eligibility_data:

            healthie_user_id = self.lookup_codes_manager.retrieve_entry_by_internal_key(uuid.UUID(patient_eligibility_data['syntrillo_internal_key'])).get('healthie_user_id', None)
            if not healthie_user_id:
                logger.warning(f"Patient {patient_eligibility_data} does not have a healthie user id")
                continue

            patient_name = HealthieUser(healthie_user_id).get_healthie_user_information_by_healthie_user_id()
            healthie_user_id = healthie_user_id
            bp_device_training_status = patient_eligibility_data['bp_device_training_status']
            eligible_to_bill = patient_eligibility_data['eligible_to_bill']

            all_patient_data.append({
                "patient_name": patient_name,
                "healthie_user_id": healthie_user_id,
                "bp_device_training_status": bp_device_training_status,
                "eligible_to_bill": eligible_to_bill
            })

        return all_patient_data


    def get_single_patient_billing_and_bp_dates_data(self, syntrillo_internal_key: str) -> dict:
        """
        Retrieves a single patient's bp date data from AWS RDS tenovi_raw_measurements table
        and the patient's

        Args:
            syntrillo_internal_key (str): De-identified internal key id for querying AWS DB
        Returns:
            single_patient_info (dict): The dates of at least one BP measurement taken
        """
        patient_billing_data = self.candid_manager.get_patient_billing_data(syntrillo_internal_key)
        patient_bp_data, _ = self.db_manager.get_all_patient_bp_data_by_syntrillo_internal_key(syntrillo_internal_key)

        single_patient_info = {
            "patient_billing_data": patient_billing_data,
            "patient_bp_data": patient_bp_data
        }

        return single_patient_info


    def retrieve_patient_eligibility_data(self) -> dict:
        logger.info(f"Retrieving all patient eligibility data ...")
        db_connection = self.db_manager.conn

        try:
            with db_connection.cursor() as cursor:
                sql_query = """
                    SELECT * FROM billing_eligibility
                """
                cursor.execute(sql_query)
                result = cursor.fetchall()

                all_patient_billing_eligibility = []
                for row in result:
                    all_patient_billing_eligibility.append({
                        "syntrillo_internal_key": row[0],
                        "cpt_code": row[1],
                        "bp_device_training_status": bool(row[2]),
                        "eligible_to_bill": bool(row[3])
                    })
                logger.info(f"Successfully retrieved all {len(all_patient_billing_eligibility)} billing eligibility results.")
                return all_patient_billing_eligibility

        except Exception as e:
            logger.error(f"Error while retrieving patient eligibility data: {e}")
            return []



    def get_healthie_patient_data(self) -> list[dict]:
        """
        Get healthie patient data from Healthie API (https://docs.gethealthie.com/guides/patient/)
        Returns:
            list[dict]: List of patient data
        """
        logger.info("Getting healthie patient data from Healthie API ...")
        all_patient_data = HealthieUtils().list_patients().get('users', [])

        if not all_patient_data:
            logger.error("ERROR: No patients found in Healthie ...") # TODO: handle this error
            return []

        return all_patient_data

    def get_bp_device_training_status(self, healthie_user_id: int) -> bool:
        """
        Get BP device training status
        Args:
            healthie_user_id (int): The Healthie user ID
        Returns:
            bool: True if the patient has completed the BP device training, False otherwise
        """
        logger.info("Retrieving BP device training status from Healthie API ...")

        device_training_form_name = DEVICE_TRAINING_FORM_NAME
        bp_device_training_form = HealthieUtils().fetch_single_healthie_form_response_by_form_name_and_user_id(device_training_form_name, healthie_user_id)

        # Response will be empty if no device training form -> "formAnswerGroups": []
        return True if bp_device_training_form else False


    def is_patient_eligible_for_billing(self, bp_data: list[str], bp_device_training_status: bool, billing_information: dict) -> bool:
        """
        Check if the patient is eligible for billing
        Args:
            bp_data (list[str]): The BP data
            bp_device_training_status (bool): The BP device training status
            billing_information (dict): The billing information
        Returns:
            bool: True if the patient is eligible for billing, False otherwise
        """
        logger.info(f"Checking if patient is eligible for billing with bp_device_training_status...")
        try:
            if not bp_device_training_status or not bp_data or not billing_information:
                return False

            # Get most recent billing date (ex., "2024-09-02")
            most_recent_billing_date = sorted(billing_information, key=lambda x: x['date_of_service'])[-1]['date_of_service']

            # Get all BP dates 30 days after the most recent billing date
            cutoff_date = most_recent_billing_date + timedelta(days=30)
            eligible_bp_count = 0

            for bp_date_str in bp_data:
                if bp_date_str >= cutoff_date:
                    eligible_bp_count += 1

            # Check if 16 or more dates are found for billing eligibility
            return eligible_bp_count >= 16
        except Exception as e:
            logger.error(f"Error while checking if patient is eligible for billing: {e}")
            return False

    def insert_billing_eligibility_data(self, all_patient_billing_eligibility: list[BillingEligibility]) -> None:
        """
        Saves the given list of BillingEligibility to Amazon RDS

        Args:
            all_patient_billing_eligibility (list[BillingEligibility]): the list of BillingEligibility to be saved
        Returns:
            None: the function does not return anything
        Raises:
            Exception: any type of exception while saving the data
        """
        if not all_patient_billing_eligibility:
            logger.warning("No billing eligibility data to insert into database")
            return None

        logger.info(f"Inserting {len(all_patient_billing_eligibility)} billing eligibility data into database")

        db_connection = self.db_manager.conn

        try:
            with db_connection.cursor() as cursor:
                sql_query = """
                    INSERT INTO billing_eligibility (
                        syntrillo_internal_key,
                        cpt_code,
                        bp_device_training_status,
                        eligible_to_bill
                    )
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        syntrillo_internal_key=VALUES(syntrillo_internal_key),
                        cpt_code=VALUES(cpt_code),
                        bp_device_training_status=VALUES(bp_device_training_status),
                        eligible_to_bill=VALUES(eligible_to_bill);
                """
                billing_eligibility_records = [
                    (
                        billing_eligibility.syntrillo_internal_key,
                        billing_eligibility.cpt_code,
                        billing_eligibility.bp_device_training_status,
                        billing_eligibility.eligible_to_bill
                    )
                    for billing_eligibility in all_patient_billing_eligibility
                ]

                cursor.executemany(sql_query, billing_eligibility_records)
                db_connection.commit()

                logger.info(f"Successfully inserted or updated {len(billing_eligibility_records)} billing eligibility data into RDS")

        except Exception as e:
            logger.exception("Error while inserting billing eligibility data into database")
            raise e


if __name__ == "__main__":
    billing_manager = BillingManager()
    # data = billing_manager.get_all_patient_eligibility_data()
    data = billing_manager.get_single_patient_billing_and_bp_dates_data("125c56e8-5e93-4211-a287-f1fcfee11da3")
    print(json.dumps(data, indent=4))
    # print(data)