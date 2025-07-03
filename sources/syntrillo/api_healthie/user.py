# Path: ./sources/syntrillo/api_healthie/user.py
import json

from syntrillo.api_healthie.auth import HealthieAuth
from syntrillo.system.logger import logger
from syntrillo.api_healthie.utils import HealthieUtils

class HealthieUser:
    """
    Get information about a Healthie user. Could be a patient or a provider.
    """

    log = {
        'success': True,
        'logs': []
    }

    def __init__(self, healthie_user_id):
        self.healthie_user_id = healthie_user_id
        self.auth = HealthieAuth()

        # Check if the user is a patient or a provider
        self._get_user_type()

        if self.is_patient():
            self._patient = self._get_patient_information()

        if self.is_provider():
            self._provider = self._get_provider_information()

    def get_log(self):
        """
        Get the log of the HealthieUser instance

        """
        return self.log

    def is_success(self):
        """
        Check if the HealthieUser instance was successful

        """
        return self.log['success']

    # --------------------------------------------
    # Main user type (Patient or Provider) and methods
    def _get_user_type(self):
        """
        Check if the user exists and is a patient or a provider

        """
        # Set up the GraphQL query
        query = '''
            query getUser($id: ID) {
                user(id: $id) {
                    is_patient
                }
            }
        '''

        # Set up the GraphQL variables
        variables = {
            'id': self.healthie_user_id
        }

        # Send the GraphQL query using the inherited send_query method
        response, log = self.auth.send_query(query, variables)

        if log['success'] and response is not None and response['user'] is not None and 'is_patient' in response['user']:
            self._is_patient = response['user']['is_patient']
            self._is_provider = not self._is_patient
        else:
            self._is_patient = None
            self._is_provider = None
            self.log['success'] = False
            self.log['logs'].append({
                'message' : 'User does not exist or is not a patient or a provider',
                'log' : log
            })

    def is_patient(self):
        """
        Check if the user is a patient

        """
        if not hasattr(self, '_is_patient'):
            self._get_user_type()
        return self._is_patient

    def is_provider(self):
        """
        Check if the user is a provider

        """
        if not hasattr(self, '_is_provider'):
            self._get_user_type()
        return self._is_provider

    def get_user_tags(self):
        """get tags associated with the user (patient or provider)

        Returns:
            list: active_tags : id, name
        """
        if self.is_patient():
            return self.get_patient_information()['active_tags']

        if self.is_provider():
            return self.get_provider_information()['active_tags']

    def does_user_have_tag(self, tag_name):
        """Check if the user has a specific tag. Patient and providers have tags.

        Args:
            tag_name (str): name of the tag

        Returns:
            bool: True if the user has the tag, False otherwise
        """
        tags = self.get_user_tags()
        if tags is not None:
            for tag in tags:
                if tag['name'] == tag_name:
                    return True
        return False


    # --------------------------------------------
    # Patient-specific information and methods
    def _get_patient_information(
    self,
    ):
        """

        Retrieve patient-specific information

        https://docs.gethealthie.com/schema/user.doc

        https://docs.gethealthie.com/schema/usergroup.doc

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
                    name
                    doc_share_id                # # An ID used for document, course, and conversation sharing
                    dob
                    gender
                    sex
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
                    active                      # The status of whether the user is active or not (if false, patient is archived)
                    additional_phone_number
                    age
                    active_tags {               # A collection of tags applied on the specific user
                        id
                        name
                    }
                    archived_at                 # Datetime of archival
                    calendar_timezone
                    created_at
                    group_name                  # The name of the patients user group
                    has_user_groups             # Check to see if the user has any user groups
                    last_active                 # last date user was active through web or mobile
                    other_provider_ids          # The IDs of other care team members for the client
                    preferred_language
                    preferred_language_code
                    providers {                 # All providers associated with the client
                        id
                        name
                    }
                    timezone
                    updated_at
                    user_group {                # User Group of this user
                        id
                        name
                    }
                    user_group_id               # The ID of the patient's user group

                }
            }
        '''

        # Set up the GraphQL variables
        variables = {
            'id': self.healthie_user_id
        }

        # Send the GraphQL query using the inherited send_query method
        response, log = self.auth.send_query(query, variables)

        if log['success'] and response is not None and response['user'] is not None:
            self._patient_information = response['user']
        else:
            self._patient_information = None
            self.log['success'] = False
            self.log['logs'].append({
                'message' : 'Patient information not retrieved',
                'log' : log
            })


    def get_patient_information(self):
        """
        Retrieve patient-specific information

        """
        if not hasattr(self, '_patient_information'):
            self._get_patient_information()
        return self._patient_information

    def get_patient_group_name(self):
        """
        Retrieve the name of the patient's user group

        """
        if not hasattr(self, '_patient_information'):
            self._get_patient_information()
        return self._patient_information['group_name']

    # --------------------------------------------
    # Provider-specific information and methods
    def _get_provider_information(
    self,
    ):
        """

        Retrieve provider-specific information

        https://docs.gethealthie.com/schema/user.doc

        https://docs.gethealthie.com/schema/tag.doc

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
                    name
                    email
                    active_tags {
                        id
                        name
                    }
                    active_patients {                # All active patients associated with this provider
                        id
                    }
                    calendar_timezone
                    created_at
                    is_active_provider
                    is_owner                        # the status of whether the user is the owner of their org or not
                    is_super_admin
                    has_user_groups                 # Check to see if the user has any user groups
                    patients {
                        id
                    }
                    patients_count
                    timezone
                    user_groups {                    # All user groups associated with this provider
                        id
                        name
                    }
                }
            }
        '''

        # Set up the GraphQL variables
        variables = {
            'id': self.healthie_user_id
        }

        # Send the GraphQL query using the inherited send_query method
        response, log = self.auth.send_query(query, variables)

        if log['success'] and response is not None and response['user'] is not None:
            self._provider_information = response['user']
        else:
            self._provider_information = None
            self.log['success'] = False
            self.log['logs'].append({
                'message' : 'Provider information not retrieved',
                'log' : log
            })

    def get_provider_information(self):
        """
        Retrieve provider-specific information

        """
        if not hasattr(self, '_provider_information'):
            self._get_provider_information()
        return self._provider_information

    def get_healthie_user_information_by_healthie_user_id(self) -> str:
        """
        Get patient name from the healthie user id using the Healthie API
        Args:
            None
        Returns:
            str: The patient name
        """
        graphql_query = '''
            query getUser($id: ID) {
                user(id: $id) {
                id
                first_name
                last_name
                }
            }
        '''
        # Query output is dict with a single key called "data"
        # For example:
        # {
        #     "data": {
        #         "user": {
        #             "id": "2315391",
        #             "first_name": "Bob",
        #             "last_name": "Barker",
        #         }
        #     }
        # }
        logger.info("Retreiving healthie user information for a given healthie user...")
        try:
            variables = {
                "id": self.healthie_user_id
            }
            output: dict = HealthieUtils.run_graphql_query(graphql_query, variables)
            logger.info(f"Successfully retrieved user information from Healthie")

            first_name = output.get('user', {}).get('first_name', '')
            last_name = output.get('user', {}).get('last_name', '')
            return first_name + " " + last_name

        except Exception as e:
            logger.error(f"Error fetching user information from Healthie: {e}")

    def get_name_by_healthie_user_id(self) -> str:
        """
        Get patient name from the healthie user id using the Healthie API
        Args:
            healthie_user_id (str): The ID of the healthie user
        Returns:
            str: The patient name
        """
        graphql_query = '''
            query getUser($id: ID) {
                user(id: $id) {
                id
                first_name
                last_name
                }
            }
        '''
        # Query output is dict with a single key called "data"
        # For example:
        # {
        #     "data": {
        #         "user": {
        #             "id": "2315391",
        #             "first_name": "Bob",
        #             "last_name": "Barker",
        #         }
        #     }
        # }
        try:
            variables = {
                "id": healthie_user_id
            }
            output: dict = self.auth.run_graphql_query(graphql_query, variables)
            logger.info(f"Successfully retrieved user information from Healthie")

            first_name = output.get('user', {}).get('first_name', '')
            last_name = output.get('user', {}).get('last_name', '')
            return first_name + " " + last_name

        except Exception as e:
            logger.error(f"Error fetching user information from Healthie: {e}")




if __name__ == '__main__':

    # Example usage
    #  - 1035117 : patient one
    #  - 1033222 : provider Olivier Delrieu
    #  - 1051518 : a provider : Omar
    user = HealthieUser(healthie_user_id='1035117')

    if user.is_success() is False:
        print(json.dumps(user.get_log(), indent=4))

    if user.is_patient():
        info = user.get_patient_information()
        print(json.dumps(info, indent=4, default=str))

    if user.is_provider():
        info = user.get_provider_information()
        print(json.dumps(info, indent=4, default=str))

    print('\n--------------------------------------------')
    tags = user.get_user_tags()
    print('user tags')
    print(json.dumps(tags, indent=4, default=str))
