# modules/healthy/utils.py

import os
import sys
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from healthie.base import HealthieAPI

class HealthieAPIUtils(HealthieAPI):
    """
    A utility class extending HealthieAPI for specific Healthie API interactions.

    This class provides methods to retrieve organization details and list patients using GraphQL queries.

    Attributes:
        api_key (str): The API key used for authentication.
        organization (str): The environment organization (default: 'staging').
        dotenv_path (str): Path to the .env file containing environment variables.
    """
    def __init__(
        self,
        api_key: str = None,
        organization: str = 'staging',
        dotenv_path: str = None,
        ):
        """
        Initializes the HealthieAPIUtils instance.

        Parameters:
            api_key (str, optional): The API key used for authentication.
            organization (str, optional): The environment organization (default: 'staging').
            dotenv_path (str, optional): Path to the .env file containing environment variables.
        """
        super().__init__(api_key, organization, dotenv_path)


    def get_organization_details(self):
        """
        Retrieve organization details using GraphQL query.

        Returns:
            dict: Response data containing organization details.
        """

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
        variables = {

        }

        # Send the GraphQL query using the class method
        response = self.send_query(query, variables)
        return response


    def list_patients(self):
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
        }

        # Send the GraphQL query using the inherited send_query method
        response = self.send_query(query, variables)

        return response


if __name__ == "__main__":
    # Load environment variables from .env file
    dotenv_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/.env")

    # Create an instance of HealthieAPI with the provided API key and organization
    utils_api = HealthieAPIUtils(dotenv_path=dotenv_path)

    # Retrieve organization details
    response = utils_api.get_organization_details()
    print(json.dumps(response, indent=4))

    # List patients
    response = utils_api.list_patients()
    print(json.dumps(response, indent=4))

