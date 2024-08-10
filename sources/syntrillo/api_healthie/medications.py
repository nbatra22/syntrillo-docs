
from typing import Tuple

from syntrillo.api_healthie.auth import HealthieAuth

class HealthieMedications:
    """

    https://docs.gethealthie.com/docs/#medications

    https://help.gethealthie.com/article/790-client-medication-history


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
            active (bool): Optional. Fetch only active Medications. Default is False.

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
                    id
                    name
                    code            # CCDA code for this medication
                    active
                    route           # The way this medication is administered
                    dosage          # Dosage of medication entered by provider
                    frequency       # Frequency of this medication
                    directions      # Directions to use medication entered by provider
                    comment         # Comments entered by provider
                    start_date      # First active date of medication
                    end_date        # last date patient should be able to use medication
                    created_at      # Date medication was created
                    updated_at      # Date medication was last updated
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




