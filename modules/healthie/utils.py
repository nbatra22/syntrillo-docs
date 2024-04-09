# modules/healthy/utils.py

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
        ):

        if dotenv_path is None :
            self.api_key = api_key
            self.organization = organization
        else:
            load_dotenv(dotenv_path=dotenv_path)
            # Get the API key and organization from environment variables
            self.api_key = os.getenv('API_KEY')
            self.organization = os.getenv('ORGANIZATION')

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
            self.url = 'https://prod-api.gethealthie.com/graphql'



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


    def get_organization_details(self):
        # Set up the GraphQL query
        query = '''
            query getOrganization($id: ID) {
                organization(id: $id) {
                    id
                    name
                    location {
                        city
                        country
                    }
                }
            }
        '''

        # Set up the GraphQL variables (if needed)
        variables = {}

        # Send the GraphQL query using the class method
        response = self.send_query(query, variables)
        return response


    def list_patients(self):

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
                }
            }
        '''

        # Set up the GraphQL variables
        variables = {
            'offset': 0,  # Offset for pagination (if applicable)
            # Add other variables as needed
        }

        # Send the GraphQL query using the inherited send_query method
        response = self.send_query(query, variables)
        return response


if __name__ == "__main__":
    # Load environment variables from .env file
    dotenv_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/.env")
    load_dotenv(dotenv_path=dotenv_path)

    # Create an instance of HealthieAPI with the provided API key and organization
    healthie_api = HealthieAPI(dotenv_path=dotenv_path)

    # Call the method to get organization details
    try:
        # org
        response = healthie_api.get_organization_details()
        print(json.dumps(response, indent=4))

        # patients
        response = healthie_api.list_patients()
        print(json.dumps(response, indent=4))

    except ValueError as ve:
        print(f"ValueError: {ve}")
        exit()
