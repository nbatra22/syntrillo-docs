from flask import jsonify
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.system.logger import logger

class BillingManager:
    """
    This class is used to manage the billing of the patients.
    """
    def __init__(self):
        pass

    def get_all_patient_data(self):
        """
        Get all patient data
        Returns:
            list[dict]: List of patient data
        """

        all_patient_data = self.get_healthie_patient_data()
        if not all_patient_data:
            return jsonify({ "all_patient_data": []})

        # Loop through list of patients and get BP device training status and BP data
        for patient in all_patient_data:
            healthie_user_id = patient.get('id')

            # Get BP device training status (Form from healthie)
            bp_device_training_status = self.get_bp_device_training_status(healthie_user_id)
            patient['bp_device_training_status'] = bp_device_training_status

            # Get BP the dates with at least 1 BP measurement
            bp_data, _ = HealthieUtils().get_all_patient_bp_data(healthie_user_id)
            patient['bp_data'] = bp_data

            # Get billing information for the patient
            billing_information = self.get_billing_information(healthie_user_id)
            patient['billing_information'] = billing_information

            # Check if the patient is eligible for billing
            is_eligible_for_billing = self.is_patient_eligible_for_billing(bp_data, bp_device_training_status, billing_information)
            patient['is_eligible_for_billing'] = is_eligible_for_billing

        return all_patient_data

    def get_healthie_patient_data(self):
        """
        Get healthie patient data from Healthie API (https://docs.gethealthie.com/guides/patient/)
        Returns:
            list[dict]: List of patient data
        """

        all_patient_data = HealthieUtils().list_patients().get('users', [])
        if not all_patient_data:
            logger.error("ERROR: No patients found in Healthie ...") # TODO: handle this error
            return []

        return all_patient_data

    def get_bp_device_training_status(self, healthie_user_id: int):
        """
        Get BP device training status
        Args:
            healthie_user_id (int): The Healthie user ID
        Returns:
            bool: True if the patient has completed the BP device training, False otherwise
        """
        device_training_form_id = None # TODO: get the form id from the config
        bp_device_training_form = HealthieUtils().fetch_single_healthie_form_response_by_custom_module_form_id_and_user_id(device_training_form_id, healthie_user_id).get('formAnswerGroups', [])
        return True if bp_device_training_form else False # Response will be empty if no device training form


    def get_billing_information(self, healthie_user_id: int):
        """
        Get billing information
        Args:
            healthie_user_id (int): The Healthie user ID
        Returns:
            dict: Billing information
        """

        '''
        Check if the date has a status of billed
        Every date is the date of the bill so it will be 30 days after that to bill for.

        '''

        raise NotImplementedError("Not implemented")

    def is_patient_eligible_for_billing(self, bp_data: list[str], bp_device_training_status: bool, billing_information: dict):
        """
        Check if the patient is eligible for billing
        Args:
            bp_data (list[str]): The BP data
            bp_device_training_status (bool): The BP device training status
            billing_information (dict): The billing information
        Returns:
            bool: True if the patient is eligible for billing, False otherwise
        """

        raise NotImplementedError("Not implemented")