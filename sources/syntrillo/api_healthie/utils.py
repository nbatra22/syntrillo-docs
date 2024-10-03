# Path: ./sources/syntrillo/api_healthie/utils.py

from syntrillo.api_healthie.auth import HealthieAuth

class HealthieUtils():
    """
    A utility class for specific Healthie API interactions.

    This class provides methods to retrieve organization details and list patients using GraphQL queries.

    """
    def __init__(self):
        """
        Initializes the HealthieAPIUtils instance.
        """
        self.auth = HealthieAuth()


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
                    can_have_suborgs
                    created_at
                    npi
                    num_users
                    owner {
                        name
                    }
                    tags {
                        name
                    }
                }
            }
        '''

        # Set up the GraphQL variables (if needed)
        variables = {

        }

        # Send the GraphQL query using the class method
        response, log = self.auth.send_query(query, variables)
        return response

    def is_org_staging(self):
        """
        Check if the organization is a staging environment.

        Returns:
            bool: True if the organization is a staging environment, False otherwise.
        """

        # Retrieve organization details
        organization_details = self.get_organization_details()

        # Check if the organization id is 57057 (staging environment)
        if organization_details['organization']['id'] == '57057':
            return True
        else:
            return False

    def get_module_types(self):
        """
        Retrieve questionnaire modules details using GraphQL query.

        Returns:
            dict: CustomModule
        """

        # Set up the GraphQL query
        query = '''
            query questionBankModules(
                $category: String
            ) {
                questionBankModules(
                    category: $category
                ) {
                    id
                    mod_type
                    options
                    options_array
                    id
                    label
                }
            }
        '''

        # Set up the GraphQL variables (if needed)
        variables = {

        }

        # Send the GraphQL query using the class method
        response, log = self.auth.send_query(query, variables)
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
            'should_paginate': False, # If set to True (default)  we only read the first 10 users
        }

        # Send the GraphQL query using the inherited send_query method
        response, log = self.auth.send_query(query, variables)

        return response

    def get_user_from_id(
        self,
        user_id : str = None
        ):
        """
        Retrieve a specific patient
        https://docs.gethealthie.com/docs/#retrieving-a-patient

        Returns:
            dict: user
        """

        # Set up the GraphQL query
        query = '''
           query getUser($id: ID) {
                user(id: $id) {
                    id
                    first_name
                    last_name
                    dob
                    gender
                    email
                    phone_number
                    next_appt_date
                    locations {
                        city
                        line1
                        line2
                        state
                        zip
                        country
                    }
                }
            }
        '''

        # Set up the GraphQL variables
        variables = {
            'id': user_id
        }

        # Send the GraphQL query using the inherited send_query method
        response, log = self.auth.send_query(query, variables)

        if response['user'] is not None:
            return response['user']
        else:
            return None


if __name__ == "__main__":
    # Create an instance of HealthieAPI with the provided API key and organization
    utils_api = HealthieUtils()

    # Retrieve organization details
    response = utils_api.get_organization_details()
    HealthieAuth.print_pretty_json(response)

    # Retrieve module types
    response = utils_api.get_module_types()
    HealthieAuth.print_pretty_json(response)

    # List patients
    response = utils_api.list_patients()
    HealthieAuth.print_pretty_json(response)

    # staging org check
    response = utils_api.is_org_staging()
    print(response)
