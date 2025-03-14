from datetime import datetime

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger


def get_lab_values(db_connection):
    """

    Returns an object below

    {
        'LDL': int (count of lab values above 71)
        'HA1c': int (count of lab values above 7)
    }

    TO DO:
        - handle staging vs. prod

    """

    try:
        with db_connection.cursor() as cursor:
            ldl_query = """
                SELECT answer from healthie_form_responses
                WHERE form_id = '1765843' AND module_id = '15159782'
            """

            ha1c_query =  """
                SELECT answer from healthie_form_responses
                WHERE form_id = '1765843' AND module_id = '15159786'
            """

            cursor.execute(ldl_query)
            ldl = cursor.fetchall()

            cursor.execute(ha1c_query)
            ha1c = cursor.fetchall()

        ldl_count = sum(1 for x in ldl if x[0].isdigit() and int(x[0]) > 71)
        ha1c_count = sum(1 for x in ha1c if x[0].isdigit() and int(x[0]) > 7)

        return {'LDL': (ldl_count), 'HA1c': ha1c_count}

    except Exception as e:
        logger.error(f"Error fetching lab values: {e}")
        return None


if __name__ == "__main__":
    syntrillo_database_manager = SyntrilloDatabaseManager("3261f346-ef09-4311-8a5f-f36d5d67e58d")
    db_connection = syntrillo_database_manager.conn
    lab_values = get_lab_values(db_connection)
    print(f"Lab Values: {lab_values}")
