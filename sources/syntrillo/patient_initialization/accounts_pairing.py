# Path: ./sources/syntrillo/patient_initialization/accounts_pairing.py

from syntrillo.api_tenovi.device_properties import DeviceProperties
from syntrillo.api_tenovi.devices import Devices
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.pseudonyms_management.temporary_lookup_codes_management import TemporaryLookUpCodesManagement

class AccountsPairing:
    """
    The objective of this class is to pair the patient's account in Syntrillo with the patient's account in Tenovi, without communicating Personal Identifiable Information (PII) between the two systems.

    The process is as follows:
    - On the Healthie provider portal, on the patient specific extra tab, the study coordinator will require a temporary pseudo code.
    - The study coordinator will enter this temporary pseudo code in the Tenovi dashboard, as the 'Patient ID' field (aka patient_external_id)
    - The study coordinator will then click on the 'Pair' button in the Healthie portal.
    - Our system will then use the Tenovi API to find devices where PatientID is equal to the temporary pseudo code entered by the study coordinator in the Tenovi dashboard.
    - On the matching devices, we will set up a key/value parameter pair with the permanent pseudo_code_for_tenovi_phi_access.
    - Lastly, we will replace the patient_external_id with the healthy_user_id.

    For a given patient identified by its syntrillo_internal_key, this class has the following methods:

    - create a temporary pseudo code using TemporaryLookUpCodesManagement.create_and_return_unique_temporary_pseudo_code(syntrillo_internal_key, 'Tenovi')

    - return this temporary pseudo code. It will be displayed on the healthie_iframe_provider_tab screen.

    - using the Tenovi api, look for devices where PatientID is equal to the temporary pseudo code, and set-up a key/value parameter pair with the permanent pseudo_code_for_tenovi_phi_access
    """

    def __init__(self, syntrillo_internal_key:str):
        self.syntrillo_internal_key = syntrillo_internal_key
        self.lookup_codes_management = LookUpCodesManagement()
        self.temporary_lookup_codes_management = TemporaryLookUpCodesManagement()
        self.devices = Devices()

    def create_and_return_unique_temporary_pseudo_code(self):
        """
        Creates a temporary pseudo code using TemporaryLookUpCodesManagement and returns it.

        Returns:
            str: The temporary code generated.
        """
        temporary_pseudo_code = self.temporary_lookup_codes_management.create_temporary_pseudo_code(
            syntrillo_internal_key=self.syntrillo_internal_key,
            purpose=TemporaryLookUpCodesManagement.PURPOSE_TENOVI_PAIRING
            )
        return temporary_pseudo_code

    def pair_devices_using_temporary_pseudo_code(self):
        """
        Use the Tenovi API to
        - find devices where PatientID (aka patient_external_id) matches the temporary pseudo code entered by the study coordinator in the Tenovi dashboard.

        then, for each device:
        - set up a key/value parameter pair with the pseudo_code_for_tenovi_phi_access.
        - replace the patient_external_id with the healthy_user_id

        """

        # get temporary_pseudo_code for this patient syntrillo_internal_key
        #  : generate some error and log is the temporary_pseudo_code is not found
        temporary_pseudo_code = self.temporary_lookup_codes_management.retrieve_tenovi_pairing_temporary_pseudo_code(self.syntrillo_internal_key)

        # get pseudo_code_for_tenovi_phi_access from syntrillo_internal_key
        entry_by_internal_key = self.lookup_codes_management.retrieve_entry_by_internal_key(self.syntrillo_internal_key)
        pseudo_code_for_tenovi_phi_access = entry_by_internal_key['pseudo_code_for_tenovi_phi_access']

        # loop for devices where PatientID is equal to the temporary code
        matching_devices = self.devices.get_devices_by_patient_external_id(temporary_pseudo_code)
        for device in matching_devices:
            # create a key/value parameter pair with the pseudo_code_for_tenovi_phi_access
            device_id = device.get('id')
            device_properties = DeviceProperties()
            device_properties.create__pseudo_code_for_tenovi_phi_access__property(device_id, pseudo_code_for_tenovi_phi_access)

        # remove the temporary_pseudo_code from the database
        self.temporary_lookup_codes_management.remove_all_temporary_codes_for_syntrillo_internal_key(
            syntrillo_internal_key=self.syntrillo_internal_key,
            purpose=TemporaryLookUpCodesManagement.PURPOSE_TENOVI_PAIRING
            )

        # TODO: need to return some log information with the number and types of devices paired
        return 'some log'



# Example usage:
if __name__ == "__main__":
    pass
