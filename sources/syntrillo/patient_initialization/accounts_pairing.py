# Path: ./sources/syntrillo/patient_initialization/accounts_pairing.py

from syntrillo.api_tenovi.device_properties import DeviceProperties
from syntrillo.api_tenovi.devices import Devices
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.pseudonyms_management.temporary_lookup_codes_management import TemporaryLookUpCodesManagement

class AccountsPairing:
    """
    For a given patient identified by its syntrillo_internal_key, this class has the following methods:

    - create a temporary code using TemporaryLookUpCodesManagement.create_temporary_code(syntrillo_internal_key, 'Tenovi')

    - return this temporary code. It will be displayed on the healthie_iframe_provider_tab screen.

    - using the Tenovi api, look for devices where PatientID is equal to the temporary code, and set-up a key/value parameter pair with the pseudo_code_for_tenovi_phi_access
    """

    def __init__(self, syntrillo_internal_key):
        self.syntrillo_internal_key = syntrillo_internal_key
        self.lookup_codes_management = LookUpCodesManagement()
        self.temporary_lookup_codes_management = TemporaryLookUpCodesManagement()
        self.devices = Devices()

    def create_and_return_temporary_code(self):
        """
        Creates a temporary code using TemporaryLookUpCodesManagement and returns it.

        Returns:
            str: The temporary code generated.
        """
        temp_code = self.temporary_lookup_codes_management.create_temporary_code(self.syntrillo_internal_key, 'Tenovi')
        return temp_code

    def setup_devices_for_patient(self, temp_code):
        """
        Uses the Tenovi API to
        - find devices where PatientID matches the temporary code stored in patient_external_id
        for each device:
        - sets up a key/value parameter pair with the pseudo_code_for_tenovi_phi_access.
        - replace the patient_external_id with the healthy_user_id
        """

        # get pseudo_code_for_tenovi_phi_access from syntrillo_internal_key
        pseudo_code_for_tenovi_phi_access = self.lookup_codes_management.retrieve_entry_by_internal_key(self.syntrillo_internal_key)['pseudo_code_for_tenovi_phi_access']

        # loop for devices where PatientID is equal to the temporary code
        matching_devices = self.devices.get_device_by_patient_external_id(temp_code)
        for device in matching_devices:
            # create a key/value parameter pair with the pseudo_code_for_tenovi_phi_access
            device_id = device.get('id')
            device_properties = DeviceProperties()
            payload = {
                "key": "pseudo_code_for_tenovi_phi_access",
                "value": pseudo_code_for_tenovi_phi_access,
                "synced": False
            }
            device_properties.create_device_property(device_id, payload)






# Example usage:
if __name__ == "__main__":
    pass
