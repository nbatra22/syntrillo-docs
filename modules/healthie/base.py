# modules/healthie/base.py

import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime

class HealthieAPI:
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
        api_key: str = None,
        organization: str = 'staging',
        dotenv_path: str = None,
        verbose=False,
        ):

        """
        Initializes the HealthieAPI client.

        Parameters:
            api_key (str, optional): The API key used for authentication.
            organization (str, optional): The environment organization (default: 'staging').
            dotenv_path (str, optional): Path to the .env file containing environment variables. If present will suprseed api_key and organization.
            verbose (bool, optional): Whether to print verbose output (default: False).

        Raises:
            ValueError: If API key is missing or organization is invalid.
        """

        if dotenv_path is None :
            self.api_key = api_key
            self.organization = organization
        else:
            load_dotenv(dotenv_path=dotenv_path)
            # Get the API key and organization from environment variables
            self.api_key = os.getenv('API_KEY')
            self.organization = os.getenv('ORGANIZATION')

        self.verbose = verbose
        if self.verbose:
            print(dotenv_path)
            print(self.api_key)
            print(self.organization)

        # Check if the API key is available
        if self.api_key is None:
            raise ValueError("API key not found. Make sure it's defined in the .env file.")

        # Check if organization is either 'staging' or 'production'
        if self.organization not in ['staging', 'production']:
            raise ValueError("Invalid organization. Must be 'staging' or 'production'.")

        # Set up the GraphQL endpoint URL based on organization
        if self.organization == 'staging':
            self.url = 'https://staging-api.gethealthie.com/graphql'
        elif self.organization == 'production':
            self.url = 'https://api.gethealthie.com/graphql'



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

        Returns:
            dict: The JSON response 'data' from the API.

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

        if self.verbose :
            self.log_this( f"send_query\n{query}\n{json.dumps(variables, indent=4)}" )

        try:
            # Make the HTTP POST request to the Healthie API
            response = requests.post(self.url, json={'query': query, 'variables': variables}, headers=headers, proxies={})
            response.raise_for_status()  # Raise an HTTPError for non-2xx responses

            # Parse response data as JSON
            response_json = response.json()

            # Check if response contains 'errors' field
            if 'errors' in response_json:
                error_messages = ', '.join([error['message'] for error in response_json['errors']])
                raise Exception(f"GraphQL query returned errors: {error_messages}")

            # Check if response contains 'data' field
            if 'data' not in response_json:
                raise Exception("GraphQL query did not return valid data")

            # Return the 'data' from the response
            return response_json['data']

        except requests.exceptions.HTTPError as errh:
            print(f"HTTP Error: {errh}")
            raise

        except requests.exceptions.RequestException as err:
            print(f"Request Exception: {err}")
            raise



if __name__ == "__main__":
    # Load environment variables from .env file
    dotenv_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/.env")
    load_dotenv(dotenv_path=dotenv_path)

    # Create an instance of HealthieAPI with the provided API key and organization
    healthie_api = HealthieAPI(dotenv_path=dotenv_path)

    # Example: Send a test query to retrieve organization details
    response = healthie_api.send_query(query='query { organization { id name } }')
    print(json.dumps(response, indent=4))


