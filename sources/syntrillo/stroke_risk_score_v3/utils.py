import math
import uuid
import pandas as pd
from syntrillo.system.logger import logger
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement

def calculate_bmi(weight: float, height: float) -> float:
    """
    Calculate BMI from weight and height.
    Args:
        weight (float): The weight in pounds
        height (float): The height in inches
    Returns:
        float: The BMI
    """
    if weight is None or height is None:
        logger.warning(f"BMI is None for patient because weight or height was not provided...")
        return None
    # BMI = Weight (lb) / Height (in)² x 703
    bmi = weight / math.pow(height, 2) * 703
    return round(bmi, 2)

def get_biometric_data(syntrillo_internal_key: uuid.UUID) -> dict:
    """
    Get the biometric data for a given syntrillo internal key
    """
    try:
        logger.info(f"Getting biometric data for patient ...")
        lookup_codes = LookUpCodesManagement()

        entry = lookup_codes.retrieve_entry_by_internal_key(syntrillo_internal_key=syntrillo_internal_key)
        healthie_user_id = entry['healthie_user_id']

        data = get_patient_info(healthie_user_id=healthie_user_id)

        height = data.get("height", None)
        weight = data.get("weight", None)
        if weight:
            weight = float(weight.split()[0])
        bmi = calculate_bmi(weight, height)


        return {
            "height": height,
            "weight": weight,
            "gender": data.get("gender", None),
            "bmi": bmi,
        }

    except Exception as e:
        logger.error(f"Error getting biometric data for syntrillo internal key {syntrillo_internal_key}: {e}")
        return None


def get_patient_info(healthie_user_id: str ):
    query="""
        query getUser($id: ID) {
            user(
                id: $id
                ) {
                gender
                height
                weight
                }
            }
    """
    variables = {
        "id": healthie_user_id,
    }

    healthie_utils = HealthieUtils()

    # Retrieve the current set of responses
    response: dict = healthie_utils.run_graphql_query(query=query, variables=variables)
    data = response.get("user", None)
    logger.info(f"Successfully got biometric data for patient ...")
    return data

def is_valid_timeframe(timeframe_df: pd.DataFrame, min_measurements: int = 3) -> bool:
    """Check if a timeframe has at least one valid (non-null) measurement and meets the min count."""
    return len(timeframe_df.dropna()) >= min_measurements and timeframe_df.notna().any().any()

def fetch_all_form_responses_from_healthie(form_id=None) -> dict:
    """
    Fetches form responses from Healthie API

    Args:
        None
    Returns:
        dict: The JSON response 'data' from the API
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
                    updated_at
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

    logger.info("Fetching form responses from Healthie.")
    try:
        all_form_responses = []
        cursor = None
        has_more_pages = True
        # Continue fetching pages until no more results
        while has_more_pages:

            if cursor:
                variables = {
                    "page_size": 100,
                    "should_paginate": True,
                    "custom_module_form_id": form_id,
                    "after": cursor
                }
            else:
                variables = {
                    "page_size": 100,
                    "should_paginate": True,
                    "custom_module_form_id": form_id
                }
            # Retrieve the current set of responses
            response: dict = HealthieUtils.run_graphql_query(graphql_query, variables)
            current_page_data = response.get("formAnswerGroups", [])

            # Append the newest set of responses to output array
            all_form_responses.extend(current_page_data)


            if len(current_page_data) == 100 and current_page_data[-1].get("cursor"):
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