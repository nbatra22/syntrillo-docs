from typing import List
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger

from .constants import EXCLUEDED_PATIENT_TAGS

def get_valid_patients() -> List[dict]:
    """
    Filters out all active Healthie patients which have excluded tags (test account or demo patient).

    Args:
        None
    Returns:
        valid_patients (List[dict]): a list of dictionaries containing valid patient information.
    Raises:
        e (Exception): General exception
    """
    healthie_utils = HealthieUtils()
    patients = healthie_utils.list_active_patients()

    valid_patients = []
    for patient in patients['users']:
        # Skip any test account or demo patient from any list of patients
        patient_active_tags = []
        if len(patient["active_tags"]) > 0:
            patient_active_tags = [tag["name"] for tag in patient["active_tags"]]

        if len(list(set(EXCLUEDED_PATIENT_TAGS) & set(patient_active_tags))):
            logger.info("Skipping patient with 'test account'/'demo' tag...")
            continue

        valid_patients.append(patient)

    return valid_patients




def list_valid_active_healthie_patients() -> dict[str, List]:
    """
    Retrieves all active Healthie patients syntrillo internal key

    Args:
        None
    Returns:
        patient_information_list (dict[str, List]): a list of dictionaries containing id information
    Raises:
        e (Exception): General exception
    """
    try:
        # list all patients syntrillo_internal_key
        lookup_codes = LookUpCodesManagement()
        valid_patients = get_valid_patients()

        patient_information_list = {"users": []}
        for patient in valid_patients:
            entry = lookup_codes.retrieve_entry_by_healthie_user_id(patient["id"])

            if entry:
                syntrillo_internal_key = str(entry['syntrillo_internal_key'])

                patient_information_list["users"].append({
                     "id": syntrillo_internal_key,
                     "healthie_user_id": patient["id"]
                })
                logger.info(f"Successfully found patient {syntrillo_internal_key} in internal lookup table...")
            else:
                logger.warning("No entry found in lookup table for healthie patient ...")

        lookup_codes.close_connection()
        return patient_information_list

    except Exception as e:
        logger.error(f"Error while retrieving syntrillo internal keys: {e}")
        raise e
