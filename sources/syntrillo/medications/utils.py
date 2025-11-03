import re
from typing import List
from decimal import Decimal
from datetime import datetime
# from datetime import date # TESTING PURPOSES

from syntrillo.medications.models import MedicationRecord, DosingScheduleRule
from syntrillo.medications.helpers import medication_from_dosing_schedule_rule
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.remote_monitoring.syntrillo_medications_db_manager import SyntrilloMedicationsDatabaseQueries
from syntrillo.system.logger import logger
from syntrillo.api_healthie.medications import HealthieMedications
# from syntrillo.medications.models import DosingScheduleRule # TESTING PURPOSES
# from syntrillo.medications.models import Frequency, TimeOfDay, DeliveryMethod # TESTING PURPOSES

def create_medication(medication: MedicationRecord) -> None:
    """
    For a new medications created via Syntrillo's Medications Form, this
    function creates a medication record in the Healthie's system then in
        Syntrillo's medications_records table.

    Args:
        medication (Medication): The medication to create.
    Returns:
        None
    """
    try:
        # (0.) Validate and extract information
        extracted_info = extract_healthie_information(medication)

        start_date_str = extracted_info.get("start_date", "")
        end_date_str = extracted_info.get("end_date", "")
        syntrillo_internal_key = extracted_info.get("syntrillo_internal_key", "")

        logger.info(f"Creating medication for syntrillo_internal_key: {syntrillo_internal_key}")

        medication = validate_medication_record(medication, True)

        lookup_codes = LookUpCodesManagement()
        entry = lookup_codes.retrieve_entry_by_internal_key(syntrillo_internal_key=syntrillo_internal_key)
        healthie_user_id = entry['healthie_user_id']

        # (1.) Create medication in Healthie's system
        healthie_utils = HealthieUtils()
        response = healthie_utils.create_medication(medication, healthie_user_id, start_date_str, end_date_str)

        # (2.) Create medication record in Syntrillo's system (If successful creation in Healthie)
        db_manager = SyntrilloMedicationsDatabaseQueries()
        if response:
            medication_id = response.get('id')
            if not medication_id:
                raise Exception("Missing required patient-medication specific identifier from Healthie response...")

            medication.medication_id = int(medication_id) # convert to int for Syntrillo DB column type
            record_id, log = db_manager.insert_medication_record(medication_record=medication)

            if not log.get("success"):
                raise Exception(log['error'])

        else:
            raise Exception(response['error_message'])

        logger.info(f"Successfully created medication for syntrillo_internal_key: {syntrillo_internal_key}")

    except Exception as e:
        logger.error(f"Error creating medication for syntrillo_internal_key: {syntrillo_internal_key}: {e}")
        raise e


def get_medication_info_by_keyword(keyword: str) -> List[dict]:
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
    db_manager = SyntrilloMedicationsDatabaseQueries()
    medications_data, log = db_manager.get_medication_records_for_patient(syntrillo_internal_key)
    return medications_data

def update_medication(medication_record: MedicationRecord) -> MedicationRecord:
    """
    Update medication record in both Healthie and Sytnrillo's DB.

    Args:
        medication_record (MedicationRecord): The updated medication record from the FE.
    Returns:
        medication_record (MedicationRecord): The updated medication record for the FE.
    Raises:
        e (Exception): General exception handling.
    """
    try:
        medication_record = validate_medication_record(medication_record, False)
        extracted_info = extract_healthie_information(medication_record)

        start_date_str = extracted_info.get("start_date", "")
        end_date_str = extracted_info.get("end_date", "")

        # 1.) Update with Healthie
        healthie_utils = HealthieUtils()
        data = healthie_utils.update_medication_record(
            medication_record=medication_record,
            start_date=start_date_str,
            end_date=end_date_str
        )

        # If error in the healthie API call
        if data.get("messages"):
            raise Exception(f"Error while updating medication in Healthie: {data.get('messages')}")

        # Successful healthie update API call (no error messages)
        db_manager = SyntrilloMedicationsDatabaseQueries()
        db_manager.insert_medication_record(medication_record)
        return medication_record

    except Exception as e:
        logger.error(f"Error in update medication function: {e}")
        raise Exception(f"Error while updating medication record: {e}")

def delete_medication(medication_id: int, syntrillo_internal_key: str) -> bool:
    """
    Deletes requested medication in both Healthie and Syntrillo's DB.
    CAUTION: This function will delete ALL records in Syntrillo's DB for the given medication_id.

    Args:
        medication_id (int): The unique Healthie patient-medication specific ID.
        syntrillo_internal_key (str): Internal ID for patient identification.
    Returns:
        is_delete_successful (bool): Boolean indicator if the delete operation was completely successful.
    Raises:
        e (Exception): General exception raised during delete operation.
    """
    try:
        syntrillo_internal_key = syntrillo_internal_key

        # 1. Delete from Healthie
        healthie_utils = HealthieUtils()
        data = healthie_utils.delete_medication(medication_id=medication_id)

        #  If error in the healthie API call
        if data.get("messages"):
            raise Exception(f"Error while deleting medication in Healthie: {data.get('messages')}")

        # 2. If Healthie deletion successful, delete all records from Syntrillo's DB.
        db_manager = SyntrilloMedicationsDatabaseQueries()
        is_delete_successful, log = db_manager.delete_medication_records(medication_id=str(medication_id))

        if not log.get("success"):
            raise Exception(f"{log.get('error')}")

        logger.info("Successfully deleted medication...")
        return is_delete_successful

    except Exception as e:
        logger.error(f"Error while deleting medication record: {e}")
        raise Exception(f"Error while deleting medication in Healthie: {e}")



def validate_medication_record(medication_record: MedicationRecord, is_creation: bool) -> MedicationRecord:
    """
    Validates required information and converts any fields for saving in Syntrillo DB.

    Args:
        medication_record (MedicationRecord): The MedicationRecord to validate
        is_creation (bool): Given this validate function is used for both update and create,
            creation wont have an initial healthie medication_id to check but update will.
    Returns:
        medication_record (MedicationRecord): The validated MedicationRecord
    """
    try:
    # To update medication in Healthie's system, the patient-medication specific id is required.
        if not medication_record.medication_id and not is_creation:
            raise Exception("Missing required patient-medication specific identifier from Healthie response...")


        # Ensure required fields are present for Healthie create API call
            # If is_active, it needs a start_date, if not active that means it ended and it needs an end date.
        if (medication_record.is_active and not medication_record.start_date) or (medication_record.is_active and medication_record.end_date):
            logger.error(f"Medication active status implies either the start or end date is missing for: {medication_record.medication_name}")
            raise Exception("End/start date is required based on active status.")

        # Update the medication record if a shorthand scheduling rule was used (BID, TID, QID, PRN)
        if medication_record.dosing_schedule_rule:
            medication_record = medication_from_dosing_schedule_rule(medication_record)

        return medication_record
    except Exception as e:
        raise e

def extract_healthie_information(medication_record: MedicationRecord) -> dict:
    """
    Extracts the required information from medication record MedicationRecord to make
    both Healthie create & update API call.

    Args:
        medication_record (MedicationRecord): The medication record to extract from.
    Returns:
        result (dict): the dictionary of information
    """
    # (1.) Create medication in Healthie's system
    # convert start_date & end_date to string in format "September 22, 2025" for Healthie create API call
    start_date_str = medication_record.start_date.strftime("%B %d, %Y") if medication_record.start_date else None
    end_date_str = medication_record.end_date.strftime("%B %d, %Y") if medication_record.end_date else None

    result = {
        "start_date": start_date_str,
        "end_date": end_date_str,
        "syntrillo_internal_key": medication_record.syntrillo_internal_key
    }

    return result


def parse_and_transform_to_medication_record(data: dict, syntrillo_internal_id: str) -> MedicationRecord:
    """
    Transforms a raw input dictionary from Healthie API response to a
    format compatible with the MedicationRecord model.

    Args:
        data (dict): A single medication object from the arr in the Healthie API response.
        syntrillo_internal_id (str): The internal syntrillo patient id.
    Returns:
        medication_record (MedicationRecord): The parsed MedicationRecord to be used to insert record into DB
    """
    transformed = {}

    # 1. Direct key remapping
    transformed['syntrillo_internal_key'] = syntrillo_internal_id
    transformed['medication_name'] = data.get('name')
    transformed['medication_id'] = data.get('id')
    transformed['is_active'] = data.get('active', True)
    transformed['comment'] = data.get('comment')
    transformed['directions'] = data.get('directions')
    transformed['mirrored'] = data.get('mirrored')

    # 2. Parse the combined 'dosage' string
    dosage_str = data.get('dosage')
    if dosage_str:
        # Use regex to find the first number (int or float) and the rest as the unit
        match = re.match(r'^\s*([0-9\.]+)\s*(.*)\s*$', dosage_str)
        if match:
            amount, unit = match.groups()
            transformed['dosage_amount'] = Decimal(amount)
            transformed['dosage_unit'] = unit.strip()

    # 3. Parse date and datetime strings
    # The '%z' directive correctly handles timezone offsets like -0400
    healthie_date_format = "%Y-%m-%d %H:%M:%S %z"

    if data.get('start_date'):
        dt_obj = datetime.strptime(data['start_date'], healthie_date_format)
        transformed['start_date'] = dt_obj.date() # Extract only the date part

    if data.get('end_date'):
        dt_obj = datetime.strptime(data['end_date'], healthie_date_format)
        transformed['end_date'] = dt_obj.date()

    medication_record = MedicationRecord(**transformed)
    return medication_record

def merge_medication_old_new_record(incomplete_record: MedicationRecord) -> MedicationRecord:
    """
    In the event of a webhook event for a Healthie medication creation, update, delete,
        the incomplete_record (new healthie updated record) is now the most recent record
        for a medication, the function retrieves the most recent record in the DB (now the 2nd most recent)
        and populates the incomplete_record with the potentially missing fields.

    Args:
        incomplete_record (MedicationRecord): The incomplete MedicationRecord for new Healthie update
    Returns:
        MedicationRecord: The most complete MedicationRecord
    """
    logger.info(f"Beginning to merge old and new medication records for med_id: {incomplete_record.medication_id}")

    # 1. Retreive most recent record by medication_id
    syntrillo_internal_key = incomplete_record.syntrillo_internal_key
    medication_id = incomplete_record.medication_id

    db_manager = SyntrilloMedicationsDatabaseQueries()
    try:
        medication_records, log = db_manager.get_medication_records_for_patient(syntrillo_internal_key=syntrillo_internal_key)
        if log.get("error"):
            err_msg = log.get("error")
            logger.error(f"Error while retrieving medication records from DB: {err_msg}")
            raise Exception(err_msg)

        old_record_dict = medication_records.get(medication_id, {}).get("current")
        if old_record_dict:
            old_record = MedicationRecord(**old_record_dict)
            update_data = incomplete_record.model_dump()

            # 2. Filter this dictionary to only include values that are not None.
            #    This prevents newer `None` values from overwriting older, valid data.
            filtered_update_data = { key: value for key, value in update_data.items() if value is not None }

            # 3. Create a deep copy of the older record and apply the filtered updates.
            #    The `update` argument overwrites fields in the copied older record
            #    with the new data.
            complete_record = old_record.model_copy(update=filtered_update_data)
            logger.info("Successfully merged old and new medication records...")
            return complete_record

        else:
            return incomplete_record
    except Exception as e:
        logger.error(f"Error while merging old and new medication records: {e}")
        raise e

def process_medication_webhook_event(healthie_user_id: str, medication_id: str, event_type: str) -> None:
    """
    In the event of a webhook event for a Healthie medication creation, update, delete,
        the internal DB record needs to be synced with the updated record from Healthie.
    This function syncs the stale internal medication record with the updated information
        in Healthie's system.

    Args:
        healthie_user_id (str): The id of the user in Healthie.
        medication_id (str): The patient<->medication unique id.
    Returns:
        None
    """
    logger.info("Processing (create/update) medications webhook event...")

    # Get both the active and inactive medications
    healthie_medications = HealthieMedications()
    response_active, log = healthie_medications.list_user_medications(healthie_user_id=healthie_user_id, active=True)
    response_inactive, log = healthie_medications.list_user_medications(healthie_user_id=healthie_user_id, active=True)

    data_active = response_active.get("medications", [])
    data_inactive = response_inactive.get("medications", [])
    all_medication_data = data_active + data_inactive

    # Find the needed medication in combined healthie medication list response
    healthie_specific_medication_dict = _extract_medication_by_id(all_medication_data, medication_id)

    lookup_codes = LookUpCodesManagement()
    entry = lookup_codes.retrieve_entry_by_healthie_user_id(healthie_user_id=healthie_user_id)
    syntrillo_internal_key = str(entry['syntrillo_internal_key'])

    med_record = parse_and_transform_to_medication_record(healthie_specific_medication_dict, syntrillo_internal_key)

    # If creation webhook, then the dosage_option_id needs to be retrieved from Healthie
    if event_type == "medication.create":
        med_search_results = get_medication_info_by_keyword(keyword=med_record.medication_name)
        for med_res in med_search_results:
            for opts in med_res.get("dosage_options", []):
                if opts.get("strength", "") == healthie_specific_medication_dict.get("dosage"):
                    med_record.dosage_option_id = opts.get("id")

    merged_record = merge_medication_old_new_record(incomplete_record=med_record)

    update_medication(merged_record)


def _extract_medication_by_id(medications_arr: List[dict], medication_id: str) -> dict:
    """
    Finds the exact desired medication in the nested medications array.
    Selection is based on the unique patient<->medication id.

    Args:
        medications_arr (List[dict]): The patient specific array of every individual medication.
        medication_id (str): Unique patient<->medication id.
    Returns:
        med (dict): The Healthie medication information dictionary object.

    """
    for med in medications_arr:
        if med.get("id") == medication_id:
            return med
    return {}


# if __name__ == "__main__":

    # CREATE MEDICATIONS
    # medication = MedicationRecord(
    #     syntrillo_internal_key="99fddf03-9304-4e48-8711-0cc4d825eb94",
    #     medication_name="Besponsa Intravenous Solution Reconstituted",
    #     dosage_amount=0.5,
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
    # print(get_medication_by_patient_id("99fddf03-9304-4e48-8711-0cc4d825eb94"))

    # UPDATE MEDICATIONS
    # medication = MedicationRecord(
    #     syntrillo_internal_key="99fddf03-9304-4e48-8711-0cc4d825eb94",
    #     medication_name="Besponsa Intravenous Solution Reconstituted",
    #     medication_id=61452,
    #     dosage_amount=0.1,
    #     dosage_unit="mg",
    #     dosage_option_id="Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvMTMwNjM",
    #     comment="Test Comment",
    #     directions="Test Directions",
    #     frequency=Frequency.DAILY,
    #     dosing_interval=2,
    #     # dosing_schedule_rule=DosingScheduleRule.BID,
    #     dose_count=4,
    #     time_of_day=TimeOfDay.BEDTIME,
    #     start_date=date(2025, 9, 26),
    #     mirrored=False,
    #     delivery_method=DeliveryMethod.PILL_TABLET_CAPSULE,
    # )
    # update_medication(medication)

    # DELETE MEDICATIONS
    # delete_medication(60347, "99fddf03-9304-4e48-8711-0cc4d825eb94")
    # medication_record = parse_and_transform_to_medication_record({
    #     "active": True,
    #     "comment": "Yeahhh",
    #     "created_at": "2025-09-22 16:49:00 -0400",
    #     "directions": "Take all",
    #     "dosage": "0.9 MG",
    #     "end_date": None,
    #     "id": "59534",
    #     "name": "Besponsa Intravenous Solution Reconstituted",
    #     "normalized_status": "ACTIVE",
    #     "start_date": "2025-09-22 00:00:00 -0400",
    #     "updated_at": "2025-09-22 16:49:00 -0400",
    #     "user_id": "1562903",
    #     "mirrored": False
    # }, "99fddf03-9304-4e48-8711-0cc4d825eb94")
    # print(medication_record.model_dump_json(indent=2))

    # medication = MedicationRecord(
    #     syntrillo_internal_key="99fddf03-9304-4e48-8711-0cc4d825eb94",
    #     medication_name="Besponsa Intravenous Solution Reconstituted",
    #     medication_id=61452,
    #     dosage_amount=0.15,
    #     dosage_unit="mg",
    #     # dosage_option_id="Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvMTMwNjM",
    #     comment="Test Comment (update here)",
    #     directions="Test Directions",
    #     # frequency=Frequency.DAILY,
    #     # dosing_interval=2,
    #     # dosing_schedule_rule=DosingScheduleRule.BID,
    #     # dose_count=4,
    #     # time_of_day=TimeOfDay.BEDTIME,
    #     start_date=date(2025, 9, 26),
    #     # delivery_method=DeliveryMethod.PILL_TABLET_CAPSULE,
    # )
    # complete_med = merge_medication_records(medication)
    # print(complete_med.model_dump_json(indent=2))

    process_medication_webhook_event("1562903", "61452", "medication.update") # updataion
    # process_medication_webhook_event("1562903", "58612", "medication.create") # create (old)
