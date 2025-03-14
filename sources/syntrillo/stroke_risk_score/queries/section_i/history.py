from datetime import datetime

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger


def get_history(db_connection):
    """

    Returns an object below

    {
        'smoker': boolean,
        'ICAD': boolean,
        'AFib': boolean,
        'OSA': boolean,
        'CPAP prescription': boolean,
        'CPAP Use': boolean
    }

    TO DO:
        - handle staging vs. prod

    """

    try:
        with db_connection.cursor() as cursor:
            smoker_query = """
                SELECT answer, healthie_user_id from healthie_form_responses
                WHERE form_id = '2155936' AND module_id = '18519144'
            """

            cursor.execute(smoker_query)
            smoker = cursor.fetchall()

            print(f"SMOKER: {smoker}")

            # --------------------------------

            # ia_query = """
            #     SELECT answer from healthie_form_responses
            #     WHERE form_id = '2155936' AND module_id = '18519144'
            # """

            # cursor.execute(ia_query)
            # smoker = cursor.fetchall()

            # --------------------------------

            afib_query = """
                SELECT answer from healthie_form_responses
                WHERE form_id = '2155936' AND module_id = '18518428'
            """

            cursor.execute(afib_query)
            afib = cursor.fetchall()

            print(f"AFIB: {afib}")

            # --------------------------------

            osa_query = """
                SELECT answer from healthie_form_responses
                WHERE form_id = '2155936' AND module_id = '18518428'
            """

            cursor.execute(osa_query)
            osa = cursor.fetchall()

            print(f"OSA: {osa}")

            # --------------------------------

            cpap_prescription_query = """
                SELECT answer from healthie_form_responses
                WHERE form_id = '2155936' AND module_id = '18519138'
            """

            cursor.execute(cpap_prescription_query)
            cpap_prescription = cursor.fetchall()

            print(f"CPAP PRESCRIPTION: {cpap_prescription}")

            # --------------------------------

            cpap_use_query = """
                SELECT answer from healthie_form_responses
                WHERE form_id = '2155936' AND module_id = '18519139'
            """

            cursor.execute(cpap_use_query)
            cpap_use = cursor.fetchall()

            print(f"CPAP USAGE: {cpap_use}")

            # --------------------------------

        return {
            'smoker': 'smoker',
            'ICAD': 'boolean',
            'AFib': 'boolean',
            'OSA': 'boolean',
            'CPAP prescription': 'boolean',
            'CPAP Use': 'boolean'
        }

    except Exception as e:
        logger.error(f"Error fetching lab values: {e}")
        return None


if __name__ == "__main__":
    syntrillo_database_manager = SyntrilloDatabaseManager("3261f346-ef09-4311-8a5f-f36d5d67e58d")
    db_connection = syntrillo_database_manager.conn
    lab_values = get_history(db_connection)
    print(f"Lab Values: {lab_values}")
