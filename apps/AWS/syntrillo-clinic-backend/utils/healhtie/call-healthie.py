import json
import requests

import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name, region_name="us-east-1"):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        # Retrieve the secret
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # Handle potential errors
        raise e
    else:
        # If no error, return the secret
        if 'SecretString' in get_secret_value_response:
            return get_secret_value_response['SecretString']
        else:
            return get_secret_value_response['SecretBinary']

# Usage
secret_name = "HealthieSecrets2BCEAFD6-lsNKS11YKKfq"
try:
    secret = json.loads(get_secret(secret_name))
    print(f"Retrieved secret: {secret}")
except Exception as e:
    print(f"Error retrieving secret: {str(e)}")

def send_query(
    query: str,
    variables: dict = {}
    ):
    """
    Sends a GraphQL query to the Healthie API.

    Parameters:
        query (str): The GraphQL query string.
        variables (dict, optional): Variables to be passed with the query (default: {}).

    Returns a tupple:
        dict: The JSON response 'data' from the API.
        dict: The log of the request.

    Raises:
        requests.exceptions.HTTPError: If the API request fails.
        requests.exceptions.RequestException: For other request errors.
        Exception if the response contains an 'errors' or does not contain 'data'
    """

    # Get the name of the calling function for logging purposes
    # caller = inspect.stack()[1].function

    api_key = secret['healthieApiKey']

    # Set up the request headers with the API key
    headers = {
        'Authorization': f'Basic {api_key}',
        'AuthorizationSource': 'API'
    }

    # Try converting the data to a JSON string. If this fails, return an error log.
    #   : this will fail if the data is not JSON serializable, for example if it includes uuid objects
    try:
        temp = json.dumps(variables)
    except Exception as e:
        log = {
            "success": False,
            "message": f"A json.dumps error occurred in {caller}: {e}",
            "data": variables,
        }
        return None, log

    try:
        # Make the HTTP POST request to the Healthie API
        url = 'https://staging-api.gethealthie.com/graphql'
        response = requests.post(url, json={'query': query, 'variables': variables}, headers=headers, proxies={})
        response.raise_for_status()  # Raise an HTTPError for non-2xx responses

        # Parse response data as JSON
        response_json = response.json()

        # Check if response contains 'errors' field
        if 'errors' in response_json:
            response_to_return = None
            log = {
                'success': False,
                'message': f"GraphQL query returned errors in {caller}",
                'response': response_json
            }
        # Check if response contains 'data' field
        elif 'data' not in response_json:
            response_to_return = None
            log = {
                'success': False,
                'message': f"GraphQL query did not return valid data in {caller}",
                'response': response_json
            }
        # successful response
        else:
            # Return the 'data' from the response
            response_to_return = response_json['data']
            log = {
                'success': True,
                # 'message': f"GraphQL query successful in {caller}",
            }

    except requests.exceptions.HTTPError as errh:
        response_to_return = None
        log = {
            'success': False,
            'message': f"HTTP Error: {errh} in {caller}",
        }

    except requests.exceptions.RequestException as err:
        response_to_return = None
        log = {
            'success': False,
            'message': f"Request Exception: {err} in {caller}",
        }

    return response_to_return, log

def list_patients():
    """
    List patients using GraphQL query.
    https://docs.gethealthie.com/docs/#list-all-patients

    Returns:
        dict: 'usersCount' and 'users' data containing a list of patients.
    """

    # Set up the GraphQL query
    query = '''
        query users(
            $offset: Int,
            $keywords: String,
            $sort_by: String,
            $active_status: String,
            $group_id: String,
            $show_all_by_default: Boolean,
            $should_paginate: Boolean,
            $provider_id: String,
            $conversation_id: ID,
            $limited_to_provider: Boolean,
            ) {
            usersCount(
                keywords: $keywords,
                active_status:$active_status,
                group_id: $group_id,
                conversation_id: $conversation_id,
                provider_id: $provider_id,
                limited_to_provider: $limited_to_provider
            )
            users(
                offset: $offset,
                keywords: $keywords,
                sort_by: $sort_by,
                active_status: $active_status,
                group_id: $group_id,
                conversation_id: $conversation_id,
                show_all_by_default: $show_all_by_default,
                should_paginate: $should_paginate,
                provider_id: $provider_id,
                limited_to_provider: $limited_to_provider
            ) {
                id
                email
            }
        }
    '''

    # Set up the GraphQL variables
    variables = {
        'offset': 0,  # Offset for pagination (if applicable)
        # Add other variables as needed
        'should_paginate': False, # If set to True (default)  we only read the first 10 users
    }

    # Send the GraphQL query using the inherited send_query method
    response, log = send_query(query, variables)

    return response

print(list_patients())
