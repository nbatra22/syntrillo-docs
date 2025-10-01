# Path: ./sources/syntrillo/api_healthie/utils.py

from typing import Optional
from syntrillo.api_healthie.auth import HealthieAuth
from syntrillo.system.logger import logger
from syntrillo.medications.models import MedicationRecord
from typing import List

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
        self.PAGE_SIZE = 100

    @staticmethod
    def run_graphql_query(
        query: str,
        variables: Optional[dict] = {}
    ) -> dict:
        """
        Runs the given GraphQL query against Healthie's backend
        Args:
            query (str): The GraphQL query to run
            variables (dict): Optional, the variables to pass to the query
        Returns:
            dict: The JSON response 'data' from the API.
        """
        try:
            auth = HealthieAuth()
            # Make the GraphQL query request using the send_query method inherited from HealthieAPI
            json_response, log_response = auth.send_query(query, variables)
            logger.info(f"GraphQL log response: {log_response}")

            return json_response
        except Exception as e:
            logger.error(f"Error running GraphQL query: {e}")
            raise e


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
            {
                "data": {
                    "usersCount": 27,
                    "users": [
                        {
                            "id": "1525423",
                            "email": "olemaitre+test-patient@syntrillo.com",
                            "name": "Patient AWS Test"
                        },
                        {
                            "id": "1966292",
                            "email": "0603a4d47b9466c732174f3c17d2ae32@gethealthie.com",
                            "name": "Patient AWS Test 2"
                        },
                    ]
                }
            }
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
                    name
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
        response, _ = self.auth.send_query(query, variables)

        return response


    def list_active_patients(self) -> dict:
        """
        List patients using GraphQL query.
        https://docs.gethealthie.com/docs/#list-all-patients

        Returns:
            dict: 'usersCount' and 'users' data containing a list of patients.
            {
                "data": {
                    "usersCount": 27,
                    "users": [
                        {
                            "id": "1525423",
                            "email": "olemaitre+test-patient@syntrillo.com",
                            "name": "Patient AWS Test"
                        },
                        {
                            "id": "1966292",
                            "email": "0603a4d47b9466c732174f3c17d2ae32@gethealthie.com",
                            "name": "Patient AWS Test 2"
                        },
                    ]
                }
            }
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
                    name
                    active_tags {
                        name
                    }
                }
            }
        '''

        # Set up the GraphQL variables
        variables = {
            'offset': 0,  # Offset for pagination (if applicable)
            'should_paginate': False, # If set to True (default)  we only read the first 10 users
            'active_status': 'active'
            # Add other variables as needed
        }

        # Send the GraphQL query using the inherited send_query method
        response, _ = self.auth.send_query(query, variables)

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



    def fetch_all_form_responses_from_healthie(self) -> dict:
        """
        Fetches form responses from Healthie API

        Args:
            None
        Returns:
            dict: The JSON response 'data' from the API
        """

        # Set up the GraphQL query to list custom module forms
        graphql_query = '''
            query formAnswerGroups(
                $date: String, # e.g "2021-10-29" using type ISO8601DateTime does not work
                $custom_module_form_id: ID, # e.g "11"
                $page_size: Int, # e.g. "1" or "10" or "100"
                $should_paginate: Boolean # e.g. "true" or "false"
                $after: Cursor # e.g "eyJrIjpbIjIwMjUtMDMtMTRU....."
                ) {
                formAnswerGroups(
                    date: $date,
                    custom_module_form_id: $custom_module_form_id,
                    page_size: $page_size,
                    should_paginate: $should_paginate,
                    after: $after
                    ) {
                    name
                    cursor
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

        # Query output is dict with a single key called "formAnswerGroups"
        # For example:
        # {
        # "formAnswerGroups": [
        #     {
        #         "name": "Telemed - PHQ-9 (v1.0)",
        #         "cursor": "eyJrIjpbIjIwMjUtMDMtMTRUMTU6NDU6MDAuMDAwMDAwWiIsMzUyOTUyMDksIjM1Mjk1MjA5Il19",
        #         "custom_module_form": {
        #             "id": "1765846"
        #         },
        #         "created_at": "2024-12-25 19:23:06 -0500",
        #         "form_answers": [
        #             {
        #                 "label": "Over the last 2 weeks, how often have you been bothered by any of the following problems?",
        #                 "displayed_answer": null,
        #                 "created_at": "2024-12-25 19:23:06 -0500",
        #                 "user_id": "2101747",
        #                 "custom_module": {
        #                     "id": "15159807"
        #                 }
        #             }
        #         ]
        #     }
        # ]
        # }

        # Healthie responses can time out ... pagination is required in this case
        # Healthie PROD servers can hanlde 100 records, not 800+ (500 error)

        logger.info("Fetching form responses from Healthie.")
        try:
            all_form_responses = []
            cursor = None
            has_more_pages = True
            # Continue fetching pages until no more results
            while has_more_pages:
                variables = {
                    "page_size": self.PAGE_SIZE,
                    "should_paginate": True,
                }
                if cursor:
                    variables["after"] = cursor

                # Retrieve the current set of responses
                response: dict = HealthieUtils.run_graphql_query(graphql_query, variables)
                current_page_data = response.get("formAnswerGroups", [])

                # Append the newest set of responses to output array
                all_form_responses.extend(current_page_data)


                if len(current_page_data) == self.PAGE_SIZE and current_page_data[-1].get("cursor"):
                    cursor = current_page_data[-1]["cursor"]
                    logger.info(f"Fetched {len(current_page_data)} records. Getting next page with cursor.")
                else:
                    has_more_pages = False
                    logger.info("No more pages to fetch.")

            logger.info(f"Successfully fetched {len(all_form_responses)} form responses.")

            output = {"formAnswerGroups": all_form_responses}
            return output

        except Exception as e:
            logger.error(f"Error fetching form responses from Healthie: {e}")


    def fetch_single_healthie_form_response_by_form_name_and_user_id(self, form_name: str, user_id: int) -> dict:
        """
        Fetches a single form response from Healthie API

        Args:
            form_name (str): The name of the form to fetch
            user_id (int): The ID of the user to fetch the form response for
        Returns:
            dict: The JSON response 'data' from the API
        """

        # Set up the GraphQL query to list custom module forms
        graphql_query = '''
            query formAnswerGroups(
                $name: String, # e.g "Device Training Note"
                $user_id: String # e.g "2101747"
                ) {
                formAnswerGroups(
                    name: $name,
                    user_id: $user_id
                    ) {
                    name
                    cursor
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

        # Query output is dict with a single key called "formAnswerGroups"
        # For example:
        #  {
        #         "formAnswerGroups": [
        #             {
        #                 "name": "AC - Device Training Note",
        #                 "cursor": "eyJrIjpbIjIwMjUtMDYtMTRUMTU6NDE6MDAuMDAwMDAwWiIsOTY1NzMwLCI5NjU3MzAiXX0=",
        #                 "custom_module_form": {
        #                     "id": "2181011"
        #                 },
        #                 "created_at": "2025-06-14 11:41:00 -0400",
        #                 "form_answers": [
        #                     {
        #                         "label": "Name",
        #                         "displayed_answer": "AWS Test, Patient",
        #                         "created_at": "2025-06-14 11:41:04 -0400",
        #                         "user_id": "1525423",
        #                         "custom_module": {
        #                             "id": "18754209"
        #                         }
        #                     },
        #                     {
        #                         "label": "Date",
        #                         "displayed_answer": "",
        #                         "created_at": "2025-06-14 11:41:04 -0400",
        #                         "user_id": "1525423",
        #                         "custom_module": {
        #                             "id": "18754207"
        #                         }
        #                     },
        #                     {
        #                         "label": "",
        #                         "displayed_answer": "<p dir=\"ltr\">Reason for Service: Initial setup of remote patient monitoring (RPM) for hypertension management.</p>\n<p dir=\"ltr\">Documentation:</p>\n<ol>\n<li dir=\"ltr\" aria-level=\"1\">\n<p dir=\"ltr\" role=\"presentation\">Device Setup: <strong>UPDATE AS NEEDED</strong></p>\n</li>\n<ul>\n<li dir=\"ltr\" aria-level=\"2\">\n<p dir=\"ltr\" role=\"presentation\">A Bluetooth-enabled blood pressure monitor was configured for data transmission. Device is both FDA-approved and HIPAA-compliant.</p>\n</li>\n<li dir=\"ltr\" aria-level=\"2\">\n<p dir=\"ltr\" role=\"presentation\">Device settings were personalized for the patient to ensure compatibility with RPM software.</p>\n</li>\n</ul>\n<li dir=\"ltr\" aria-level=\"1\">\n<p dir=\"ltr\" role=\"presentation\">Patient Education: <strong>UPDATE AS NEEDED</strong></p>\n</li>\n<ul>\n<li dir=\"ltr\" aria-level=\"2\">\n<p dir=\"ltr\" role=\"presentation\">The patient was instructed on device use, including taking blood pressure readings, and troubleshooting common issues.</p>\n</li>\n<li dir=\"ltr\" aria-level=\"2\">\n<p dir=\"ltr\" role=\"presentation\">The patient demonstrated proficiency in using the devices and accessing RPM data on their mobile app.</p>\n</li>\n</ul>\n<li dir=\"ltr\" aria-level=\"1\">\n<p dir=\"ltr\" role=\"presentation\">Consent: <strong>UPDATE AS NEEDED</strong></p>\n</li>\n<ul>\n<li dir=\"ltr\" aria-level=\"2\">\n<p dir=\"ltr\" role=\"presentation\">The patient provided informed consent for RPM services. Consent was documented in the medical record.</p>\n</li>\n</ul>\n</ol>\n<p dir=\"ltr\">Supervising Provider:<strong> [Physician/QHCP Name]</strong></p>\n<p dir=\"ltr\">Clinical Staff:<strong> [Name of Staff Performing Setup, if applicable]</strong></p>",
        #                         "created_at": "2025-06-14 11:41:04 -0400",
        #                         "user_id": "1525423",
        #                         "custom_module": {
        #                             "id": "18754208"
        #                         }
        #                     }
        #                 ]
        #             }
        #         ]
        #     }
        # }

        # Healthie responses can time out ... pagination is required in this case
        # Healthie PROD servers can hanlde 100 records, not 800+ (500 error)

        logger.info("Fetching Device Training Note form response from Healthie.")
        try:
            # Continue fetching pages until no more results
            variables = {
                "name": form_name,
                "user_id": user_id
            }

            # Retrieve the current set of responses
            response: dict = HealthieUtils.run_graphql_query(graphql_query, variables)
            current_page_data = response.get("formAnswerGroups", [])

            logger.info(f"Successfully fetched Device Training Note form response from Healthie.")

            return current_page_data

        except Exception as e:
            logger.error(f"Error fetching Device Training Note form response from Healthie: {e}")

    def create_medication(self, medication: MedicationRecord, healthie_user_id: str, start_date_str: str, end_date_str: str = None) -> dict:
        """
        Creates a medication in Healthie API

        Args:
            medication (MedicationRecord): The medication to create.
            healthie_user_id (str): The Healthie user ID.
            start_date_str (str): The start date of the medication.
            end_date_str (str): The end date of the medication.
        Returns:
            data (dict): The response from Healthie's API about the specific medication.
        """
        graphql_query = '''
            mutation createMedication(
                $user_id: String,
                $active: Boolean,
                $comment: String,
                $directions: String,
                $dosage: String,
                $dosage_option_id: ID,
                $name: String,
                $start_date: String,
                $end_date: String,
            ) {
                createMedication(
                    input: {
                        user_id: $user_id,
                        active: $active,
                        comment: $comment,
                        directions: $directions,
                        dosage: $dosage,
                        dosage_option_id: $dosage_option_id,
                        name: $name,
                        start_date: $start_date,
                        end_date: $end_date
                    }
                ) {
                    medication {
                        id
                        name
                        dosage
                    }
                    messages {
                        field
                        message
                    }
                }
            }
        '''

        '''
        Example response:
        {
            "data": {
                "createMedication": {
                    "medication": {
                        "id": "58931",
                        "name": "Besponsa Intravenous Solution Reconstituted",
                        "dosage": "0.9 MG",
                    }
                }
            }
        }
        '''

        logger.info("Creating medication in Healthie...")
        try:
            # Continue fetching pages until no more results
            variables = {
                "user_id": healthie_user_id,
                "active": medication.is_active,
                "comment": medication.comment,
                "directions": medication.directions,
                "dosage": None,
                "dosage_option_id": medication.dosage_option_id,
                "name": medication.medication_name,
                "start_date": start_date_str,
                "end_date": end_date_str,
            }

            # Retrieve the current set of responses
            response: dict = HealthieUtils.run_graphql_query(graphql_query, variables)
            data = response.get("createMedication", []).get("medication", [])
            logger.info(f"Successfully created medication in Healthie...")

            return data

        except Exception as e:
            logger.error(f"Error creating medication in Healthie: {e}")


    def get_medication_info_by_keywords(self, keywords: str) -> List[dict]:
        """
        Gets medication info by keyword from Healthie's system.

        Args:
            keyword (str): The keyword to search for.
        Returns:
            List[dict]: The medication info.
            Example Response:
                [
                    {
                        "id": "Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvMTc2NTI",
                        "name": "oxyCODONE HCl Oral Tablet Abuse-Deterrent",
                        "dosage_options": [
                            {
                                "id": "Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvMTc2NTQ",
                                "strength": "5 MG",
                                "ndc": "73780000110"
                            },
                            {
                                "id": "Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvOTM3MTQ",
                                "strength": "10 MG",
                                "ndc": "73780000210"
                            }
                        ]
                    },
                    {
                        "id": "Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvMTc2NTI",
                        "name": "oxyCODONE HCl Oral Tablet Abuse-Deterrent",
                        "dosage_options": [
                            {
                                "id": "Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvMTc2NTQ",
                                "strength": "5 MG",
                                "ndc": "73780000110"
                            }
                        ]
                    }
                ]
        """
        try:
            graphql_query = '''
                query medicationOptions($keywords: String) {
                    medication_options(keywords: $keywords) {
                        id
                        name
                        dosage_options {
                            id
                            strength
                            ndc
                        }
                    }
                }
            '''

            variables = { "keywords": keywords }
            response = HealthieUtils.run_graphql_query(graphql_query, variables)
            data = response.get("medication_options", {})
            return data

        except Exception as e:
            logger.error(f"Error getting medication info by keyword: {keywords}. Error: {e}")
            raise e

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
