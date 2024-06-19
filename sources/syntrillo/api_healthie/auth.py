# Path: ./sources/syntrillo/api_healthie/auth.py

import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime

from syntrillo.system.dot_env_loader import DotEnvFileLoader

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

        # Set up the request headers with the API key
        headers = {
            'Authorization': f'Basic {self.api_key}',
            'AuthorizationSource': 'API'
        }

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
                    'message': 'GraphQL query returned errors',
                    'response': response_json
                }
            # Check if response contains 'data' field
            elif 'data' not in response_json:
                response_to_return = None
                log = {
                    'success': False,
                    'message': 'GraphQL query did not return valid data',
                    'response': response_json
                }
            # successful response
            else:
                # Return the 'data' from the response
                response_to_return = response_json['data']
                log = {
                    'success': True,
                    'message': 'GraphQL query successful',
                }

        except requests.exceptions.HTTPError as errh:
            response_to_return = None
            log = {
                'success': False,
                'message': f"HTTP Error: {errh}",
            }

        except requests.exceptions.RequestException as err:
            response_to_return = None
            log = {
                'success': False,
                'message': f"Request Exception: {err}",
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


