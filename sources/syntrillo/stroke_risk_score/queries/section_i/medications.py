from datetime import datetime

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger


def get_medications():

    db_manager = SyntrilloDatabaseManager(syntrillo_internal_key="3261f346-ef09-4311-8a5f-f36d5d67e58d")
    db_connection = db_manager.conn

    try:
        with db_connection.cursor() as cursor:
            query = """
                SELECT * from healthie_form_templates
                WHERE form_id = '2155936' AND module_id = '18520987'
            """

            cursor.execute(query)
            result = cursor.fetchall()

        logger.info(f"Successfully fetched medications: {result}")
        return result

    except Exception as e:
        logger.error(f"Error fetching medications: {e}")
        return None

    finally:
        db_connection.close()


if __name__ == "__main__":
    get_medications()
