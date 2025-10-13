import re
from decimal import Decimal
from datetime import datetime
from datetime import date
from syntrillo.medications.models import Frequency, TimeOfDay, DeliveryMethod

from syntrillo.system.logger import logger
from syntrillo.medications.models import MedicationRecord
from syntrillo.remote_monitoring.syntrillo_medications_db_manager import SyntrilloMedicationsDatabaseQueries

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

def merge_medication_records(incomplete_record: MedicationRecord) -> MedicationRecord:
    """
    If incomplete_record is now the most recent record for a medication,
    the function retrieves the most recent record in the DB (now the 2nd most recent)
    and populates the incomplete_record with the potentially missing fields.

    Args:
        incomplete_record (MedicationRecord): The incomplete MedicationRecord
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

def update_medication_db(medication_record: MedicationRecord, updated_at: str) -> bool:
    """
    A function which compared the Healthie medication records for a single patient
    to determine if a new record should be inserted into the DB.

    If webhook:
        This record will always be the most recent.
        Then we should populate the missing fields from the 2nd most recent record
            then insert into DB.

    If one-time daily schedule:
        Compare updated_at timestamp
        if more recent -> populate the missing fields from the 2nd most recent record
            then insert into DB.
    """
    return True


if __name__ == "__main__":
    medication_record = parse_and_transform_to_medication_record({
        "active": True,
        "comment": "Yeahhh",
        "created_at": "2025-09-22 16:49:00 -0400",
        "directions": "Take all",
        "dosage": "0.9 MG",
        "end_date": None,
        "id": "59534",
        "name": "Besponsa Intravenous Solution Reconstituted",
        "normalized_status": "ACTIVE",
        "start_date": "2025-09-22 00:00:00 -0400",
        "updated_at": "2025-09-22 16:49:00 -0400",
        "user_id": "1562903",
        "mirrored": False
    }, "99fddf03-9304-4e48-8711-0cc4d825eb94")
    print(medication_record.model_dump_json(indent=2))

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