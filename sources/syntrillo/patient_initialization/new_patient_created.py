# Path: ./sources/syntrillo/patient_initialization/new_patient_created.py

import os
from dotenv import load_dotenv

from syntrillo.api_healthie.auth import HealthieAuth
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement

class NewPatientCreated():
    """
    A class handling initiation procedures when a new patient is created at Healthie.

    - called by User:patient.created webhook
    - defines ids, keys, codes, pseudonyms, and relationships between them
    - defines providers : clinician, OT, AI


    """

    def __init__(
        self,
        api_key: str = None,
        organization: str = 'staging',
        dotenv_path: str = '.env'
    ):
        self.auth = HealthieAuth(api_key=api_key, organization=organization, dotenv_path=dotenv_path)
        self.utils = HealthieUtils(api_key=api_key, organization=organization, dotenv_path=dotenv_path)

        # paths have to be hard-coded at PythonAnywhere
        if os.path.exists('/home/syntrillo/_this_is_PythonAnywhere_') and dotenv_path == ".env":
            dotenv_path = '/home/syntrillo/Syntrillo_Clinic/.env'

        # Load the environment variables from the specified file
        load_dotenv(dotenv_path=dotenv_path)


    def get_healthie_user_id_from_resource_id(
        self,
        data : dict  = None
        ):
        """
        {"resource_id": 1209676, "resource_id_type": "User", "event_type": "patient.created", "changed_fields": []}
        """

        # here, resource_id is the healthie_user_id !!!
        return data['resource_id']


    def endpoint(
        self,
        data : dict  = None
    ) :
        """
        Called when User:patient.created webhook is received.

        data looks like : {"resource_id": 1209676, "resource_id_type": "User", "event_type": "patient.created", "changed_fields": []}

        Creates a new entry in our database for the new patient, in user_look_up_codes
        """

        # get healthie_user_id from the resource_id
        healthie_user_id = self.get_healthie_user_id_from_resource_id(data=data)

        # add a new entry in user_look_up_codes
        lookup_code_management = LookUpCodesManagement()
        lookup_code_management.create_entry(healthie_user_id=healthie_user_id)



