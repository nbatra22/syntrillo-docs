# modules/healthie/base.py

import requests
import os
import json
from dotenv import load_dotenv

class HealthieAPI:
    def __init__(
        self,
        api_key: str = None,
        organization: str = 'staging',
        dotenv_path: str = None,
        verbose=False,
        ):

        if dotenv_path is None :
            self.api_key = api_key
            self.organization = organization
        else:
            load_dotenv(dotenv_path=dotenv_path)
            # Get the API key and organization from environment variables
            self.api_key = os.getenv('API_KEY')
            self.organization = os.getenv('ORGANIZATION')

        if verbose:
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



    def send_query(self, query: str, variables: dict = {}):
        # Set up the request headers with the API key
        headers = {
            'Authorization': f'Basic {self.api_key}',
            'AuthorizationSource': 'API'
        }

        try:
            # Make the HTTP POST request to the Healthie API
            response = requests.post(self.url, json={'query': query, 'variables': variables}, headers=headers)
            response.raise_for_status()  # Raise an HTTPError for non-2xx responses

            # Parse response data as JSON
            response_data = response.json()
            return response_data

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

    # Call the method to get organization details
    try:
        # test
        response = healthie_api.send_query(query='query { organization { id name } }')
        print(json.dumps(response, indent=4))

    except ValueError as ve:
        print(f"ValueError: {ve}")
        exit()

