
from syntrillo.medications.models import MedicationRecord
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager

def create_medication(medication: MedicationRecord) -> None:
    """
    Creates a medication record in the medications_records table for a new medication.

    Args:
        medication (Medication): The medication to create.
    Returns:
        None
    """
    # (0.) Get Healthie user ID
    syntrillo_internal_key = medication.syntrillo_internal_key
    db_manager = SyntrilloDatabaseManager(syntrillo_internal_key)

    # Get healthie user id from lookup codes
    lookup_codes = LookUpCodesManagement()
    entry = lookup_codes.retrieve_entry_by_internal_key(syntrillo_internal_key=syntrillo_internal_key)
    healthie_user_id = entry['healthie_user_id']

    # Ensure required fields are present
    if not medication.dosage_option_id:
        raise Exception("Dosage option ID is required")

    # (1.) Create medication in Healthie's system
    healthie_utils = HealthieUtils()
    response = healthie_utils.create_medication(medication, healthie_user_id)

    # (2.) If successful creation in Healthie, then create medication record in Syntrillo's system

    if response['success']:
        medication_id = response['medication_id']
        medication.medication_id = medication_id
        # TODO – Think about how to generalize inerting into DB.
    else:
        raise Exception(response['error_message'])
