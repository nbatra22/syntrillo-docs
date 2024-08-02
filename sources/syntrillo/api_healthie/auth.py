# Path: ./sources/syntrillo/api_healthie/auth.py

import requests
import os
import json
import inspect
from typing import Tuple
from dotenv import load_dotenv
from datetime import datetime

from syntrillo.system.dot_env_loader import DotEnvFileLoader

def get_secrets(secret_arn):
    try:
        get_secret_value_response = requests.get(
            f"http://localhost:2773/secretsmanager/get?secretId={secret_arn}",
            headers={"X-AWS-Parameters-Secrets-Token": os.environ.get('AWS_SESSION_TOKEN')},
        )
        get_secret_value_response.raise_for_status()  # Raise an exception for non-2xx status codes
    except requests.exceptions.RequestException as e:
        # Handle exceptions related to the HTTP request
        # if "an unexpected error occurred while executing request" in the response text => check lammbda permissions to read in secrets manager
        raise Exception(f"Error fetching secret [{get_secret_value_response.text}]: {e}")

    try:
        secret_value = get_secret_value_response.text
        secret_dict = json.loads(secret_value)
    except json.JSONDecodeError as e:
        # Handle exceptions related to JSON decoding
        raise Exception(f"Error decoding secret value [{get_secret_value_response.text}]: {e}")

    try:
        secrets_string = secret_dict["SecretString"]
    except KeyError as e:
        # Handle exceptions related to missing "SecretString" key
        raise Exception(f"Error retrieving SecretString: {e}")
    
    try:
        secrets_dict=json.loads(secrets_string)
        return secrets_dict
    except json.JSONDecodeError as e:
        # Handle exceptions related to not well formated secret string (non json)
        raise Exception(f"Error decoding secrets (should be in json format in aws secrets manager): {e}")

class HealthieAuth:
    """
    A class for interacting with the Healthie API.

    This class provides methods to initialize the API client,
    send GraphQL queries, and handle API responses.

    Attributes:
        api_key (str): The API key used for authentication.
        organization (str): The environment organization (default: 'staging').
        verbose (bool): Whether to print verbose output for debugging (default: False).
        url (str): The GraphQL endpoint URL based on the organization.
    """

    # class attributes
    api_key = None
    organization = None
    verbose = False
    url = None


    def __init__(
        self,
        verbose=False,
        ):

        """
        Initializes the HealthieAPI client.

        Parameters:
            verbose (bool, optional): Whether to print verbose output (default: False).

        Raises:
            ValueError: If API key is missing or organization is invalid.
        """

        if os.getenv('AWS_SECRETS_MANAGER_HEALTHIE_SECRET_ARN') != None:
            # If this test passes, it means we are in the lambda function

            # retrieve secrets in aws secrets manager
            healthie_secrets=get_secrets(os.getenv('AWS_SECRETS_MANAGER_HEALTHIE_SECRET_ARN'))

            # ------------------------------
            # Retrieve the organization
            self.organization = healthie_secrets['healthieOrganization']

            # Set up the GraphQL endpoint URL based on organization
            if self.organization == 'staging':
                self.url = 'https://staging-api.gethealthie.com/graphql'

            elif self.organization == 'production':
                self.url = 'https://api.gethealthie.com/graphql'
            else:
                # raise error if organization is not staging or production
                raise ValueError("Invalid Healthie organization. Must be 'staging' or 'production'.")

            # ------------------------------
            # get the API key based
            self.api_key = healthie_secrets['healthieApiKey']

            # Check if the API key is available
            if self.api_key is None:
                raise ValueError("API key not found. Make sure it's defined in the .env file.")

            # ------------------------------
            self.verbose = verbose
            if self.verbose:
                print(self.organization)

        else:
            # Load the .env file based on the environment to retrieve the client domain and API key
            _ = DotEnvFileLoader()

            # ------------------------------
            # Retrieve the organization from the environment variables
            self.organization = os.getenv('HEALTHIE_ORGANIZATION')

            # Set up the GraphQL endpoint URL based on organization
            if self.organization == 'staging':
                self.url = 'https://staging-api.gethealthie.com/graphql'

            elif self.organization == 'production':
                self.url = 'https://api.gethealthie.com/graphql'
            else:
                # raise error if organization is not staging or production
                raise ValueError("Invalid Healthie organization. Must be 'staging' or 'production'.")

            # ------------------------------
            # get the API key based
            self.api_key = os.getenv('HEALTHIE_API_KEY')

            # Check if the API key is available
            if self.api_key is None:
                raise ValueError("API key not found. Make sure it's defined in the .env file.")

            # ------------------------------
            self.verbose = verbose
            if self.verbose:
                print(self.organization)

    def send_query(
        self,
        query: str,
        variables: dict = {}
        ) -> Tuple[dict, dict]:
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
        caller = inspect.stack()[1].function

        # Set up the request headers with the API key
        headers = {
            'Authorization': f'Basic {self.api_key}',
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
            response = requests.post(self.url, json={'query': query, 'variables': variables}, headers=headers, proxies={})
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
                    'message': f"GraphQL query successful in {caller}",
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

    @staticmethod
    def print_pretty_json(data):
        print(json.dumps(data, indent=4, sort_keys=True))


if __name__ == "__main__":

    # Create an instance of HealthieAPI with the provided API key and organization
    healthie_api = HealthieAuth()

    # Example: Send a test query to retrieve organization details
    response, log = healthie_api.send_query(query='query { organization { id name } }')
    HealthieAuth.print_pretty_json(response)
    HealthieAuth.print_pretty_json(log)


