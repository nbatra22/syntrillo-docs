from typing import Dict, Any
import json
import logging
from datetime import datetime

from syntrillo.api_healthie.auth import HealthieAuth
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager

import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Basic AWS Lambda handler function.

    Args:
        event (dict): The event data passed to the Lambda function
        context (LambdaContext): Runtime information provided by AWS Lambda

    Returns:
        dict: Response object containing statusCode and body
    """
    logger.info("Event received: %s", json.dumps(event))

    # Get list of all forms
    # Healthie API calls

    # For each form collect all the questions and answers

    # Push data to MySQL database



    try:
        # Extract data from the event (if it's an API Gateway event)
        if 'body' in event:
            body = json.loads(event.get('body', '{}'))
        else:
            body = event

        # Process the request
        message = body.get('message', 'Hello from Lambda!')
        timestamp = datetime.utcnow().isoformat()

        # Prepare the response
        response_body = {
            'message': message,
            'timestamp': timestamp,
            'requestId': context.aws_request_id
        }

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # For CORS support
            },
            'body': json.dumps(response_body)
        }

    except Exception as e:
        logger.error("Error processing request: %s", str(e))
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }

def fetchAndInsertAllFormTemplates():
    '''
    Fetch all form templates from Healthie API for a given healthie_user_id
    See https://docs.gethealthie.com/docs/#form-templates

    Parameters:
        None

    Returns:
        dict:   dict: The JSON response 'data' from the API.
    '''
    # Set up the GraphQL query to list custom module forms
    query = '''
        query formTemplates(
            $include_default_templates: Boolean
            $active_status: Boolean
            $should_paginate: Boolean
            $category: String
            $keywords: String
            $offset: Int
            $sortBy: String
            ) {
                customModuleForms(
                    include_default_templates: $include_default_templates
                    active_status: $active_status
                    should_paginate: $should_paginate
                    category: $category
                    keywords: $keywords
                    offset: $offset
                    sort_by: $sortBy
                ) {
                    id
                    name
                    prefill
                    uploaded_by_healthie_team
                    custom_modules {
                    id
                    mod_type
                    options
                    label
                    }
                }
            }
    '''

    # Set up the variables for the GraphQL query
    variables = {}
    auth = HealthieAuth()
    # Make the GraphQL query request using the send_query method inherited from HealthieAPI
    json_response, log_response = auth.send_query(query, variables)
    print(log_response)

    # output_dir = "/Users/alexc/syntrillo/extra"
    # os.makedirs(output_dir, exist_ok=True)
    # output_file = os.path.join(output_dir, 'healthie_template_response.json')
    # with open(output_file, 'w', encoding='utf-8') as f:
    #     json.dump(json_response, f, indent=4, ensure_ascii=False)

    # Set up DB connection
    lookup_codes = LookUpCodesManagement()
    healthie_user_id = '1051529' # 1051529 : Omar's "Patient One" / Patient One": 1035117
    key_entry = lookup_codes.retrieve_entry_by_healthie_user_id(healthie_user_id)
    db_manager = SyntrilloDatabaseManager(key_entry['syntrillo_internal_key'])
    # Insert the data
    db_log = db_manager.insert_overwrite_healthie_form_templates(json.dumps(json_response))
    print(db_log)
    return json_response


def fetchAndInsertAllFormResponses():
    '''
        Fetch all form templates from Healthie API for a given healthie_user_id
    See https://docs.gethealthie.com/docs/#form-templates

    Parameters:
        None

    Returns:
        dict:   dict: The JSON response 'data' from the API.
    '''
    # Set up the GraphQL query to list custom module forms
    query = '''
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

    # Set up the variables for the GraphQL query
    variables = {}

    # Make the GraphQL query request using the send_query method inherited from HealthieAPI
    auth = HealthieAuth()
    json_response, log_response = auth.send_query(query, variables)
    print(log_response)

    # output_dir = "/Users/alexc/syntrillo/extra"
    # os.makedirs(output_dir, exist_ok=True)
    # output_file = os.path.join(output_dir, 'healthie_forms_response.json')
    # with open(output_file, 'w', encoding='utf-8') as f:
    #     json.dump(json_response, f, indent=4, ensure_ascii=False)

    # Set up DB connection
    lookup_codes = LookUpCodesManagement()
    healthie_user_id = '1051529' # 1051529 : Omar's "Patient One" / Patient One": 1035117
    key_entry = lookup_codes.retrieve_entry_by_healthie_user_id(healthie_user_id)
    db_manager = SyntrilloDatabaseManager(key_entry['syntrillo_internal_key'])

    # Insert the data
    db_log = db_manager.insert_overwrite_healthie_form_responses(json.dumps(json_response))
    print(db_log)
    return json_response


if __name__ == "__main__":
    fetchAndInsertAllFormResponses()
