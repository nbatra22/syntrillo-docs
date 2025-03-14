from datetime import datetime

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger


# flagged_medicines = [
#     'blood thinner',
#     "aspirin",
#     "plavix",
#     "statin",
#     "antiplatte",
#     "hypoglycemic",
#     "antihypertensive"
# ]

def get_medications(db_connection):
    """

    Returns an array of medications

    TO DO:
        - handle staging vs. prod

    """

    flagged_medicines = {
        'blood thinner': (False, ""),
        "aspirin": (False, ""),
        "plavix": (False, ""),
        "statin": (False, ""),
        "antiplatte": (False, ""),
        "hypoglycemic": (False, ""),
        "antihypertensive": (False, "")
    }

    try:
        with db_connection.cursor() as cursor:
            query = """
                SELECT answer from healthie_form_responses
                WHERE form_id = '2155936' AND module_id = '18520987'
            """

            cursor.execute(query)
            result = cursor.fetchall()

        # logger.info(f"Successfully fetched medications: {result[0][0]}") # answer comes as tuple

        ans = result[0][0]

        split_ans = ans.split('\\\\')

        # logger.info(f"split answer: {split_ans}")

        medications = [(med.split('|')[0].strip('\\\r').lower(), med.split('|')[3].strip('\\\r').lower()) for med in split_ans]

        # logger.info(f"Medications: {medications}")

        for flagged_medicine in flagged_medicines:
            for prescription, compliance in medications:
                if flagged_medicine in prescription:
                    flagged_medicines[flagged_medicine] = (True, compliance)

        return flagged_medicines

    except Exception as e:
        logger.error(f"Error fetching medications: {e}")
        return None


if __name__ == "__main__":
    get_medications()
