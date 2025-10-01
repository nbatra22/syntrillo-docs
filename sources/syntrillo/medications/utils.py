from syntrillo.medications.models import MedicationRecord
from syntrillo.medications.helpers import medication_from_dosing_schedule_rule
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from datetime import date
from syntrillo.medications.models import Frequency, TimeOfDay, DeliveryMethod
import json
from syntrillo.system.logger import logger

def create_medication(medication: MedicationRecord) -> None:
    """
    Creates a medication record in the medications_records table for a new medication.

    Args:
        medication (Medication): The medication to create.
    Returns:
        None
    """
    try:
        # (0.) Get Healthie user ID
        syntrillo_internal_key = medication.syntrillo_internal_key
        logger.info(f"Creating medication for syntrillo_internal_key: {syntrillo_internal_key}")

        lookup_codes = LookUpCodesManagement()
        entry = lookup_codes.retrieve_entry_by_internal_key(syntrillo_internal_key=syntrillo_internal_key)
        healthie_user_id = entry['healthie_user_id']

        # Ensure required fields are present for Healthie create API call
        if not medication.dosage_option_id:
            logger.error(f"Dosage option ID is required for medication: {medication.medication_name}")
            raise Exception("Dosage option ID is required")

        # Handle shortcut of using dosing schedule rule to determine dosage amount
        if medication.dosing_schedule_rule:
            medication = medication_from_dosing_schedule_rule(medication)

        # (1.) Create medication in Healthie's system
        # convert start_date & end_date to string in format "September 22, 2025" for Healthie create API call
        start_date_str = medication.start_date.strftime("%B %d, %Y") if medication.start_date else None
        end_date_str = medication.end_date.strftime("%B %d, %Y") if medication.end_date else None

        healthie_utils = HealthieUtils()
        response = healthie_utils.create_medication(medication, healthie_user_id, start_date_str, end_date_str)

        # (2.) If successful creation in Healthie, then create medication record in Syntrillo's system
        db_manager = SyntrilloDatabaseManager(syntrillo_internal_key)

        if response:
            medication.medication_id = response.get('id')
            # TODO – Think about how to generalize inserting into DB.
        else:
            raise Exception(response['error_message'])

        logger.info(f"Successfully created medication for syntrillo_internal_key: {syntrillo_internal_key}")

    except Exception as e:
        logger.error(f"Error creating medication for syntrillo_internal_key: {syntrillo_internal_key}: {e}")
        raise e


def get_medication_info_by_keyword(keyword: str):
    """
    Gets medication info by keyword from Healthie's system.

    Args:
        keyword (str): The keyword to search for.
    Returns:
        dict: The medication info.
    Raises:
        e (Exception): exception raised while fetching Healthie medication results for keywords.
    """
    try:
        healthie_utils = HealthieUtils()
        response = healthie_utils.get_medication_info_by_keywords(keyword)
        return response
    except Exception as e:
        logger.error(f"Error getting medication info by keyword: {keyword}: {e}")
        raise e


if __name__ == "__main__":

    # medication = MedicationRecord(
    #     syntrillo_internal_key="f474f229-c199-4a39-addf-0557d2c30638",
    #     medication_name="Besponsa Intravenous Solution Reconstituted",
    #     dosage_amount=0.9,
    #     dosage_unit="mg",
    #     dosage_option_id="Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvMTMwNjM",
    #     comment="Test Comment",
    #     directions="Test Directions",
    #     frequency=Frequency.DAILY,
    #     interval=2,
    #     # dosing_schedule_rule=DosingScheduleRule.BID,
    #     dose_count=3,
    #     time_of_day=TimeOfDay.BEDTIME,
    #     start_date=date(2025, 9, 26),
    #     delivery_method=DeliveryMethod.PILL_TABLET_CAPSULE,
    # )

    # create_medication(medication)
    print(json.dumps(get_medication_info_by_keyword("oxyCODONE HCl Oral Tablet Abuse-Deterrent"), indent=4))



# Fields to be filled in after Healthie creation:
# But, the FE will be able to send these back because the info is present in
# the get medication list by keyword call
# • medication_name="Test Medication",
# • dosage_amount=10.0,
# • dosage_unit="mg",
