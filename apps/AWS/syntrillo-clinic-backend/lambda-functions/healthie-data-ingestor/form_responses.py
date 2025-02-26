from datetime import datetime

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger

from healthie_api import run_graphql_query
from helpers import clean_text
from models import FormResponse

     # flat_output = []
    # flat_output['form_id']

def process_form_responses() -> None:
    """
    3 steps:
        1. Ingest from Healthie's Form Response GraphQL API (https://docs.gethealthie.com/docs/#querying-filled-out-forms)
        2. Flatten data json data returned from Healthie into a list of FormResponses
        3. Push list of FormResponses into our Amazon RDS (table: healthie_form_responses)

    Args:
        None
    Returns:
        None
    """
    graphql_output = fetch_all_form_responses_from_healthie()
    flattened_output = flatten_form_responses(graphql_output)
    insert_form_responses_to_sql(flattened_output)

def fetch_all_form_responses_from_healthie() -> dict:
    """
    Runs GraphQL query against Healthie's backend to fetch ALL the form templates.

    Args:
        None:
    Returns:
        dict: The JSON response 'data' from the API.
    """
    # Set up the GraphQL query to list custom module forms
    graphql_query = '''
        query formAnswerGroups(
            $date: String, # e.g "2021-10-29" using type ISO8601DateTime does not work
            $custom_module_form_id: ID, # e.g "11"
            ) {
            formAnswerGroups(
                date: $date,
                custom_module_form_id: $custom_module_form_id,
                ) {
                name
                custom_module_form {
                    id
                }
                created_at
                form_answers {
                    label
                    displayed_answer
                    created_at
                    user_id
                    custom_module {
                        id
                    }
                }
            }
        }
    '''

    # Query output is dict with a single key called "formAnswerGroups"
    # For example:
    # {
    # "formAnswerGroups": [
    #     {
    #         "name": "Telemed - PHQ-9 (v1.0)",
    #         "custom_module_form": {
    #             "id": "1765846"
    #         },
    #         "created_at": "2024-12-25 19:23:06 -0500",
    #         "form_answers": [
    #             {
    #                 "label": "Over the last 2 weeks, how often have you been bothered by any of the following problems?",
    #                 "displayed_answer": null,
    #                 "created_at": "2024-12-25 19:23:06 -0500",
    #                 "user_id": "2101747",
    #                 "custom_module": {
    #                     "id": "15159807"
    #                 }
    #             }
    #         ]
    #     }
    # ]
    # }
    logger.info("Fetching form responses from Healthie")
    try:
        output: dict = run_graphql_query(graphql_query)
        logger.info("Successfully fetched form responses")
        return output
    except Exception as e:
        logger.error(f"Error fetching form responses from Healthie: {e}")


def flatten_form_responses(json_data: dict) -> list[FormResponse]:
    """
    Flattens the given `json_data` into a list of FormResponses

    Args:
        json_data (dict): the json data returned from the Healthie's GraphQL API
    Returns:
        list[FormResponse]
    """
    flattened_responses = []

    # Get the form answer groups from the JSON
    form_answer_groups = json_data.get("formAnswerGroups", [])

    if not form_answer_groups:
        logger.warning("No form answer groups found in the API response")
        return []

    # Process each form answer group
    for form_group in form_answer_groups:
        form_id = form_group.get("custom_module_form", {}).get("id")

        # Process each form answer within the group
        for answer in form_group.get("form_answers", []):
            module_id = answer.get("custom_module", {}).get("id")
            user_id = answer.get("user_id")
            displayed_answer = clean_text(answer.get("displayed_answer", None))

            # Parse the created_at timestamp
            created_at_str = answer.get("created_at")
            try:
                created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S %z")
            except (ValueError, TypeError):
                # Default to current timestamp if parsing fails
                created_at = datetime.now()

            # Create FormResponse object if we have all required fields
            if all([module_id, form_id, user_id]):
                response = FormResponse(
                    form_id = form_id,
                    module_id = module_id,
                    user_id = user_id,
                    answer = displayed_answer,
                    created_at = created_at
                )
                flattened_responses.append(response)

    return flattened_responses




def insert_form_responses_to_sql(flattened_responses: dict) -> None:
    """
    Saves the given list of FormResponses to Amazon RDS

    Args:
        flattened_responses (list[FormResponse]): the list of FormResponses to be saved
    Returns:
        None: the function does not return anything
    Raises:
        Exception: any type of exception while saving the data
    """

    # TODO: we are reusing this object, which does too many things but helps us move fast
    # Use it when it speeds you up, but don't implement more methods in it
    # This object should allow us to run arbitrary SQL queries against our internal
    # operational Amazon RDS

    if not flattened_responses:
        logger.warning("No responses to insert into database")
        return

    db_manager = SyntrilloDatabaseManager(syntrillo_internal_key="NOT_USED")
    db_connection = db_manager.conn

    try:
        with db_connection.cursor() as cursor:
            sql_query = """
                INSERT INTO healthie_form_responses (
                    form_id,
                    module_id,
                    user_id,
                    answer,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    answer=VALUES(answer),
                    created_at=VALUES(created_at);
            """

            # Convert to list of tuples for executemany
            response_records = [
                (
                    response.form_id,
                    response.module_id,
                    response.user_id,
                    response.answer,
                    response.created_at
                )
                for response in flattened_responses
            ]

            # Execute a bulk query with tuples
            cursor.executemany(sql_query, response_records)
            db_connection.commit()

            # TODO: Implement a proper lookup code management system for masking
            # user_id in the database. Below line is too slow for bulk inserts.
            # lookup_codes = LookUpCodesManagement()
            # 'user_id':  lookup_codes.retrieve_entry_by_healthie_user_id(response.user_id),

            logger.info(f"Inserted or updated {len(response_records)} form responses enties into RDS")

    except Exception as e:
        logger.exception = {
            f"Database error while inserting form responses. Error: {str(e)}"
        }
        raise e

    finally:
        db_manager.close_connection()
        logger.info("Database connection closed")
