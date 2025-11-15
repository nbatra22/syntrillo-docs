# Path: ./sources/syntrillo/api_healthie/medications.py

import json
from typing import Tuple, List, Optional

from syntrillo.api_healthie.auth import HealthieAuth
from syntrillo.system.logger import logger
from syntrillo.medications.models import MedicationRecord


class HealthieMedications:
    """

    https://docs.gethealthie.com/docs/#medications

    https://help.gethealthie.com/article/790-client-medication-history

    Other queries are available if needed (Fetch count of medications for a given patient, ...). See https://docs.gethealthie.com/schema/query.doc


    """

    def __init__(self) -> None:
        """
        Initialize the HealthieMedications class.
        """
        self.auth = HealthieAuth()

    def list_user_medications(
        self,
        healthie_user_id: str,
        active: bool = False,
        ) -> Tuple[dict, dict]:
        """
        List medications based on the specified criteria using the Healthie API.

        The API returns an array of medication types

        See :
           - https://docs.gethealthie.com/docs/#listing-medications
           - https://docs.gethealthie.com/schema/medicationtype.doc

        Query (for reference):
            medications(
                active: Boolean,
                patient_id: ID,
                unreconciled_from_ccda_ingest: Boolean
                ): [MedicationType!]

        Parameters:
            healthie_user_id (str): The Healthie user ID.
            active (bool): Optional. Fetch only inactive Medications. Default is False.

        Returns:
            dict: returns list of medication types based on the specified criteria.
        """
        # Set up the GraphQL query to list custom module forms
        query = '''
            query medications(
                $active: Boolean,
                $patient_id: ID
                ) {
                    medications(
                        active: $active,
                        patient_id: $patient_id
                    ) {
                        id                # Patient<->medication specific id
                        name              # Medication name
                        code              # CCDA code for this medication
                        active            # Active status of medication
                        route             # The way this medication is administered
                        dosage            # Dosage of medication entered by provider
                        frequency         # Frequency of this medication
                        directions        # Directions to use medication entered by provider
                        comment           # Comments entered by provider
                        start_date        # First active date of medication
                        end_date          # last date patient should be able to use medication
                        created_at        # Date medication was created
                        updated_at        # Date medication was last updated
                        mirrored          # If the medication is mirrored in another system
                        normalized_status
                    }
                }
        '''

        # Set up the variables for the GraphQL query
        variables = {
            'patient_id': healthie_user_id,
            'active': active,
        }

        # Make the GraphQL query request using the send_query method inherited from HealthieAPI
        response, log = self.auth.send_query(query, variables)

        return response, log

    def create_medication(
            self,
            medication: MedicationRecord,
            healthie_user_id: str,
            start_date_str: str,
            end_date_str: str = ""
        ) -> dict:
        """
        Creates a medication in Healthie API

        Args:
            medication (MedicationRecord): The medication to create.
            healthie_user_id (str): The Healthie user ID.
            start_date_str (str): The start date of the medication.
            end_date_str (str): The end date of the medication.
        Returns:
            data (dict): The response from Healthie's API about the specific medication.
        Raises:
            e (Exception): generic exception
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
                $end_date: String
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
                        mirrored
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
            response, log = self.auth.send_query(graphql_query, variables)
            data = response.get("createMedication", {}).get("medication", {})
            logger.info("Successfully created medication in Healthie...")

            return data

        except Exception as e:
            logger.error(f"Error creating medication in Healthie: {e}")
            raise e


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
            response, log = self.auth.send_query(graphql_query, variables)
            data = response.get("medication_options", [])
            return data

        except Exception as e:
            logger.error(f"Error getting medication info by keyword: {keywords}. Error: {e}")
            raise e

    def update_medication_record(self, medication_record: MedicationRecord, start_date: str, end_date: str) -> dict:
        """
        Updates medication info by keyword from Healthie's system.

        Args:
            medication_record (MedicationRecord): updated medication record.
            start_date (str): the start date string of the medication.
            end_date (str): the end date string of the medication but can be None.
        Returns:
            data (dict): the unnecessary (except for errors) response data.
        Raises:
            e (Exception): general exception handling for Healthie GraphQL repsonses.
        """

        try:
            graphql_query ="""
                mutation updateMedication(
                $active: Boolean,
                $comment: String,
                $directions: String,
                $dosage: String,
                $id: ID,
                $name: String,
                $start_date: String,
                $end_date: String
                ) {
                updateMedication(input: {
                    active: $active,
                    comment: $comment,
                    directions: $directions,
                    dosage: $dosage,
                    id: $id,
                    name: $name,
                    start_date: $start_date,
                    end_date: $end_date
                }) {
                    medication {
                        id
                        name
                        mirrored
                    }
                    messages {
                        field
                        message
                        }
                    }
                }
            """

            variables = {
                "active": medication_record.is_active,
                "comment": medication_record.comment,
                "directions": medication_record.directions,
                "dosage": f"{medication_record.dosage_amount} {medication_record.dosage_unit}",
                "id": medication_record.medication_id,
                "name": medication_record.medication_name,
                "start_date": start_date,
                "end_date": end_date
            }

            response, log = self.auth.send_query(graphql_query, variables)
            data = response.get("updateMedication", {})
            return data

        except Exception as e:
            logger.error(f"Error updating medication with med id: {medication_record.medication_id}. Error: {e}")
            raise e

    def delete_medication(self, medication_id: int) -> dict:
        """
        Deletes medication from Healthie's system.

        Args:
            medication_id (int): The medication ID.
        Returns:
            data (dict): the unnecessary (except for errors) response data.
                Example response:
                {
                    "deleteMedication": {
                        "medication": {
                            "id": "50200",
                            "name": "Adderall OHYAH Tablet",
                            "user_id": "1562903"
                        },
                        "messages": null
                    }
                }
        Raises:
            e (Exception): general exception handling for Healthie GraphQL repsonses.
        """
        try:
            graphql_query = """
                mutation deleteMedication($id: ID) {
                    deleteMedication(input: {
                        id: $id
                    }) {
                        medication {
                            id
                            name
                            user_id
                        }
                        messages {
                            field
                            message
                        }
                    }
                }
            """
            variables = { "id": str(medication_id) }

            response, log = self.auth.send_query(graphql_query, variables)
            if not response:
                raise Exception(f"No medication record found in Healthie's system for medication id: {medication_id}")
            data = response.get("deleteMedication", {})

            return data

        except Exception as e:
            logger.error(f"Error deleting medication with med id: {medication_id}. Error: {e}")
            raise e

if __name__ == '__main__':
    healthie_medications = HealthieMedications()
    response, log = healthie_medications.list_user_medications(healthie_user_id='1035117', active=True)

    print(json.dumps(response, indent=4, default=str))
