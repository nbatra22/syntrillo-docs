from syntrillo.medications.models import MedicationRecord, DosingScheduleRule
from syntrillo.medications.helpers import medication_from_dosing_schedule_rule
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.remote_monitoring.syntrillo_medications_db_manager import SyntrilloMedicationsDatabaseQueries
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
            # If is_active, it needs a start_date, if not active that means it ended and it needs an end date.
        if (medication.is_active and not medication.start_date) or (not medication.is_active and not medication.end_date):
            logger.error(f"Medication active status implies either the start or end date is missing for: {medication.medication_name}")
            raise Exception("End/start date is required based on active status.")

        # Handle shortcut of using dosing schedule rule to determine dosage amount
        if medication.dosing_schedule_rule:
            medication = medication_from_dosing_schedule_rule(medication)

        # (1.) Create medication in Healthie's system
            # convert start_date & end_date to string in format "September 22, 2025" for Healthie create API call
        start_date_str = medication.start_date.strftime("%B %d, %Y") if medication.start_date else None
        end_date_str = medication.end_date.strftime("%B %d, %Y") if medication.end_date else None

        healthie_utils = HealthieUtils()
        response = healthie_utils.create_medication(medication, healthie_user_id, start_date_str, end_date_str)

        # (2.) Create medication record in Syntrillo's system (If successful creation in Healthie)
        db_manager = SyntrilloMedicationsDatabaseQueries(syntrillo_internal_key)
        if response:
            medication_id = response.get('id')
            if not medication_id:
                raise Exception("Missing required patient-medication specific identifier from Healthie response...")

            medication.medication_id = int(medication_id)
            record_id, log = db_manager.insert_medication_record(medication_record=medication)

            if log.get("success") == False:
                raise Exception(log['error'])

        else:
            raise Exception(response['error_message'])

        logger.info(f"Successfully created medication for syntrillo_internal_key: {syntrillo_internal_key}")

    except Exception as e:
        logger.error(f"Error creating medication for syntrillo_internal_key: {syntrillo_internal_key}: {e}")
        raise e


def get_medication_info_by_keyword(keyword: str) -> dict:
    """
    Gets medication info by keyword from Healthie's system.

    Args:
        keyword (str): The keyword to search for.
    Returns:
        response (dict): The medication info.
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

def get_medication_by_patient_id(syntrillo_internal_key: str):
    """
    Fetches all the medications records in DESC order.
    Args:
        syntrillo_internal_key (str): unique internal id for patient identification
    Returns:
        medications_data (Dict[str, Dict[str, Any]]): A dictionary where keys are medication_ids.
                                    Each value contains the 'current' record
                                    and a 'history' list of older records.
    """
    db_manager = SyntrilloMedicationsDatabaseQueries(syntrillo_internal_key)
    medications_data, log = db_manager.get_medication_records_for_patient(syntrillo_internal_key)
    return medications_data

def update_medication_by_medication_id(medication_record: MedicationRecord) -> MedicationRecord:
    """
    Update medication record in both Healthie and Sytnrillo's DB.

    Args:
        medication_record (MedicationRecord): The updated medication record from the FE.
    Returns:
        medication_record (MedicationRecord): The updated medication record for the FE.
    Raises:
        e (Exception): General exception handling.
    """
    # To update medication in Healthie's system, the patient-medication specific id is required.
    if not medication_record.medication_id:
        raise Exception("Missing required patient-medication specific identifier from Healthie response...")

    # 1.) Update with Healthie
    healthie_utils = HealthieUtils()
    data = healthie_utils.update_medication_record(medication_record)

    if data.get("messages"):
        raise Exception(f"Error while updating medication in Healthie: {data.get("messages")}")







if __name__ == "__main__":

    # CREATE MEDICATIONS
    # medication = MedicationRecord(
    #     syntrillo_internal_key="f474f229-c199-4a39-addf-0557d2c30638",
    #     medication_name="Besponsa Intravenous Solution Reconstituted",
    #     dosage_amount=0.9,
    #     dosage_unit="mg",
    #     dosage_option_id="Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvMTMwNjM",
    #     comment="Test Comment",
    #     directions="Test Directions",
    #     # frequency=Frequency.DAILY,
    #     # dosing_interval=2,
    #     dosing_schedule_rule=DosingScheduleRule.BID,
    #     dose_count=4,
    #     time_of_day=TimeOfDay.BEDTIME,
    #     start_date=date(2025, 9, 26),
    #     delivery_method=DeliveryMethod.PILL_TABLET_CAPSULE,
    # )
    # create_medication(medication)

    # KEYWORD SEARCH
    # valid_keywords = "oxyCODONE HCl Oral Tablet Abuse-Deterrent"
    # invalid_keywords = "oxyCODONE HCl Oral Tablet Abuse-Deterrent"
    # print(json.dumps(get_medication_info_by_keyword(valid_keywords), indent=4))

    # GET MEDICATIONS
    print(get_medication_by_patient_id("f474f229-c199-4a39-addf-0557d2c30638"))



# Fields to be filled in after Healthie creation:
# But, the FE will be able to send these back because the info is present in
# the get medication list by keyword call
# • medication_name="Test Medication",
# • dosage_amount=10.0,
# • dosage_unit="mg",
