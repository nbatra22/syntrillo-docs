from datetime import datetime

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger

from healthie_api import run_graphql_query
from helpers import clean_text
from models import FormResponse

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
            $page_size: Int, # e.g. "1" or "10" or "100"
            $should_paginate: Boolean # e.g. "true" or "false"
            $after: Cursor # e.g "eyJrIjpbIjIwMjUtMDMtMTRU....."
            ) {
            formAnswerGroups(
                date: $date,
                custom_module_form_id: $custom_module_form_id,
                page_size: $page_size,
                should_paginate: $should_paginate,
                after: $after
                ) {
                name
                cursor
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
    #         "cursor": "eyJrIjpbIjIwMjUtMDMtMTRUMTU6NDU6MDAuMDAwMDAwWiIsMzUyOTUyMDksIjM1Mjk1MjA5Il19",
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

    # Healthie responses can time out ... pagination is required in this case
    # Healthie PROD servers can hanlde 100 records, not 800+ (500 error)
    PAGE_SIZE = 100
    logger.info("Fetching form responses from Healthie.")
    try:
        all_form_responses = []
        cursor = None
        has_more_pages = True
        # Continue fetching pages until no more results
        while has_more_pages:

            if cursor:
                variables = {
                    "page_size": PAGE_SIZE,
                    "should_paginate": True,
                    "after": cursor
                }
            else:
                variables = {
                    "page_size": PAGE_SIZE,
                    "should_paginate": True
                }
            # Retrieve the current set of responses
            response: dict = run_graphql_query(graphql_query, variables)
            current_page_data = response.get("formAnswerGroups", [])

            # Append the newest set of responses to output array
            all_form_responses.extend(current_page_data)


            if len(current_page_data) == PAGE_SIZE and current_page_data[-1].get("cursor"):
                cursor = current_page_data[-1]["cursor"]
                logger.info(f"Fetched {len(current_page_data)} records. Getting next page with cursor.")
            else:
                has_more_pages = False
                logger.info("No more pages to fetch.")

        logger.info(f"Successfully fetched {len(all_form_responses)} form responses.")

        output = {"formAnswerGroups": all_form_responses}
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
    try:
        # Get the form answer groups from the JSON
        form_answer_groups = json_data.get("formAnswerGroups", [])

        if not form_answer_groups:
            logger.warning("No form answer groups found in the API response")
            return []

        # Temporary list to store form responses with Healthie user_ids
        temp_responses = []

        # Set to collect unique user_ids
        unique_user_ids = set()

        # Process each form answer group
        for form_group in form_answer_groups:
            form_id = form_group.get("custom_module_form", {}).get("id", None)

            # Process each form answer within the group
            for answer in form_group.get("form_answers", []):
                module_id = answer.get("custom_module", {}).get("id", None)
                healthie_user_id = answer.get("user_id", None)
                displayed_answer = clean_text(answer.get("displayed_answer", None))

                # Parse the created_at timestamp
                created_at_str = answer.get("created_at", None)
                try:
                    created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S %z")
                except (ValueError, TypeError):
                    # Default to current timestamp if parsing fails
                    created_at = datetime.now()

                # Create dict object if we have all required fields
                if all([module_id, form_id, healthie_user_id]):
                    temp_data = {
                        'form_id': form_id,
                        'module_id': module_id,
                        'healthie_user_id': healthie_user_id,
                        'answer': displayed_answer,
                        'created_at': created_at
                    }
                    temp_responses.append(temp_data)
                    unique_user_ids.add(healthie_user_id)

        # If no responses found, return empty list
        if not temp_responses:
            return []

        # Batch retrieve the mapping of healthie_user_ids to syntrillo_internal_keys
        user_mapping = batch_retrieve_user_mapping(list(unique_user_ids))

        # Create final FormResponse objects with the syntrillo_internal_key
        flattened_responses = []
        missing_user_ids = set()

        for response in temp_responses:
            healthie_user_id = response['healthie_user_id']
            if healthie_user_id in user_mapping:
                syntrillo_internal_key = user_mapping[healthie_user_id]['syntrillo_internal_key']
                flattened_response = FormResponse(
                    form_id=response['form_id'],
                    module_id=response['module_id'],
                    syntrillo_internal_key=syntrillo_internal_key,  # Replace with syntrillo_internal_key
                    answer=response['answer'],
                    created_at=response['created_at']
                )
                flattened_responses.append(flattened_response)
            else:
                missing_user_ids.add(healthie_user_id)

        if missing_user_ids:
            logger.warning(f"No mapping found for {len(missing_user_ids)} healthie_user_ids: {list(missing_user_ids)[:5]}")

        return flattened_responses
    except Exception as e:
        logger.error(f"Error flattening JSON form responses: {e}")
        return []


def batch_retrieve_user_mapping(healthie_user_ids: list[int]) -> dict:
    """
    Batch retrieve entries from the user_look_up_codes table using multiple healthie_user_ids.

    Args:
        healthie_user_ids (list): List of healthie user IDs
        db_connection: Database connection object (optional)

    Returns:
        dict: A dictionary mapping healthie_user_ids to their corresponding syntrillo_internal_keys
    """
    if not healthie_user_ids:
        return {}

    try:
        # Initialize the database manager specifically for the user_look_up_codes table
        db_manager = LookUpCodesManagement()
        db_connection = db_manager.conn

        # Create a cursor
        with db_connection.cursor() as cursor:
            # Create placeholders for the IN clause
            placeholders = ', '.join(['%s'] * len(healthie_user_ids))

            select_query = f"""
                SELECT
                    healthie_user_id,
                    BIN_TO_UUID(syntrillo_internal_key) as syntrillo_internal_key,
                    BIN_TO_UUID(pseudo_code_for_tenovi_phi_access) as pseudo_code_for_tenovi_phi_access
                FROM user_look_up_codes
                WHERE healthie_user_id IN ({placeholders});
            """

            cursor.execute(select_query, tuple(healthie_user_ids))
            entries = cursor.fetchall()

            # Create a mapping of healthie_user_id to syntrillo internal key
            user_mapping = {}
            for entry in entries:
                healthie_user_id = entry[0]
                user_mapping[healthie_user_id] = {
                    'syntrillo_internal_key':entry[1],
                    'healthie_user_id': healthie_user_id
                }

            logger.info(f"Retrieved {len(user_mapping)} entries out of {len(healthie_user_ids)} requested")

            return user_mapping

    except Exception as e:
        logger.error(f"Error retrieving user mapping from database: {e}")
        return []

    finally:
        db_connection.close()




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
                    syntrillo_internal_key,
                    answer,
                    created_at
                )
                VALUES (%s, %s, %s,REPLACE(%s, '\n', '|'), %s)
                ON DUPLICATE KEY UPDATE
                    answer=VALUES(answer),
                    created_at=VALUES(created_at);
            """

            # Convert to list of tuples for executemany
            response_records = [
                (
                    response.form_id,
                    response.module_id,
                    response.syntrillo_internal_key,
                    response.answer,
                    response.created_at
                )
                for response in flattened_responses
            ]

            # Execute a bulk query with tuples
            cursor.executemany(sql_query, response_records)
            db_connection.commit()

            logger.info(f"Successfully inserted or updated {len(response_records)} form responses enties into RDS")

    except Exception as e:
        logger.exception = {
            f"Database error while inserting form responses. Error: {str(e)}"
        }
        raise e

    finally:
        db_connection.close()
        logger.info("Database connection closed")
