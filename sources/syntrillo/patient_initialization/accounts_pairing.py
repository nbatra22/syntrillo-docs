# Path: ./sources/syntrillo/patient_initialization/accounts_pairing.py

from pprint import pprint  # Import pprint for pretty printing

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
    - Lastly, we will replace the patient_external_id with the healthie_user_id.

    For a given patient identified by its syntrillo_internal_key, this class has the following methods:

    - create a temporary pseudo code using TemporaryLookUpCodesManagement.create_and_return_unique_temporary_pseudo_code(syntrillo_internal_key, 'Tenovi')

    - return this temporary pseudo code. It will be displayed on the healthie_iframe_provider_tab screen.

    - using the Tenovi api, look for devices where PatientID is equal to the temporary pseudo code, and set-up a key/value parameter pair with the permanent pseudo_code_for_tenovi_phi_access
    """

    def __init__(self, syntrillo_internal_key:str, verbose=False):
        """
        Initialize the AccountsPairing instance.

        Args:
            syntrillo_internal_key (str): The internal key for the patient's Syntrillo account.
            verbose (bool): If True, enable verbose logging. Default is False.
        """
        self.syntrillo_internal_key = syntrillo_internal_key
        self.lookup_codes_management = LookUpCodesManagement()
        self.temporary_lookup_codes_management = TemporaryLookUpCodesManagement()
        self.devices = Devices()
        self.verbose = verbose

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

    def pair_devices_using_temporary_pseudo_code(
        self,
        update_patient_id_with_healthie_user_id:bool = True,
        add_healthie_user_id_to_device_properties:bool = True,
        ):
        """ Use the Tenovi API to:
        - Find devices where PatientID (aka patient_external_id) matches the temporary pseudo code entered by the study coordinator in the Tenovi dashboard.
        - For each device, set up a key/value parameter pair with the pseudo_code_for_tenovi_phi_access.
        - Replace the patient_external_id with the healthie_user_id.

        Args:
            update_patient_id_with_healthie_user_id (bool): If True, update the device's patient ID with the healthie_user_id. Default is True.
            add_healthie_user_id_to_device_properties (bool): If True, add the healthie_user_id to the device's properties. Default is True.

        Returns:
            dict: A log dictionary containing method name, paired devices count, paired devices list, removal log, and success status.
        """

        method_name = self.pair_devices_using_temporary_pseudo_code.__name__

        # get temporary_pseudo_code for this patient syntrillo_internal_key
        #  : generate some error and log is the temporary_pseudo_code is not found
        temporary_pseudo_code = self.temporary_lookup_codes_management.retrieve_tenovi_pairing_temporary_pseudo_code(self.syntrillo_internal_key)

        # get pseudo_code_for_tenovi_phi_access from syntrillo_internal_key
        entry_by_internal_key = self.lookup_codes_management.retrieve_entry_by_internal_key(self.syntrillo_internal_key)
        pseudo_code_for_tenovi_phi_access = entry_by_internal_key['pseudo_code_for_tenovi_phi_access']

        if self.verbose:
            print(f"temporary_pseudo_code: {temporary_pseudo_code}")
            print(f"pseudo_code_for_tenovi_phi_access: {pseudo_code_for_tenovi_phi_access}")

        # loop for devices where PatientID is equal to the temporary code
        paired_devices = []
        matching_devices = self.devices.get_devices_by_patient_external_id(temporary_pseudo_code)
        for device in matching_devices:
            # create a key/value parameter pair with the pseudo_code_for_tenovi_phi_access
            device_id = device.get('id')
            device_name = device.get('device').get('name')
            device_properties = DeviceProperties()

            device_properties.create__pseudo_code_for_tenovi_phi_access__property(device_id, pseudo_code_for_tenovi_phi_access)

            if add_healthie_user_id_to_device_properties:
                device_properties.create__healthie_user_id__property(device_id, entry_by_internal_key.get('healthie_user_id'))

            if update_patient_id_with_healthie_user_id:
                self.devices.update_device_patient_id(device_id, entry_by_internal_key.get('healthie_user_id'))

            if self.verbose:
                print(f"Device {device_id} {device_name} updated with pseudo_code_for_tenovi_phi_access")

            paired_devices.append( {
                'device_name' : device_name,
                'device_id' : device_id,
            } )

        # remove the temporary_pseudo_code from the database
        removal_log = self.temporary_lookup_codes_management.remove_all_temporary_codes_for_syntrillo_internal_key(
            syntrillo_internal_key=self.syntrillo_internal_key,
            purpose=TemporaryLookUpCodesManagement.PURPOSE_TENOVI_PAIRING
            )

        log = {
            "method": method_name,
            "paired_devices_count": len(paired_devices),
            "paired_devices": paired_devices,
            "removal_log": removal_log,
            "success": len(paired_devices) > 0
        }
        return log

    @staticmethod
    def get_paired_devices(
        pseudo_code_for_tenovi_phi_access:str = None,
        healthie_user_id:str = None,
        syntrillo_internal_key:str = None,
    ) :
        """
        Retrieve the devices paired with the given pseudo_code_for_tenovi_phi_access, healthie_user_id, or syntrillo_internal_key.

        Args:
            pseudo_code_for_tenovi_phi_access (str): The pseudo code for Tenovi PHI access.
            healthie_user_id (str): The healthie user ID.
            syntrillo_internal_key (str): The internal key for the patient's Syntrillo account.

        Returns:
            list: A list of devices paired with the given pseudo_code_for_tenovi_phi_access, healthie_user_id, or syntrillo_internal_key.
        """
        devices = Devices()
        lookup_manager = LookUpCodesManagement()

        if healthie_user_id is not None:
            entry = lookup_manager.retrieve_entry_by_healthie_user_id(healthie_user_id)
            pseudo_code_for_tenovi_phi_access = entry.get('pseudo_code_for_tenovi_phi_access')
        elif syntrillo_internal_key is not None:
            entry = lookup_manager.retrieve_entry_by_internal_key(syntrillo_internal_key)
            pseudo_code_for_tenovi_phi_access = entry.get('pseudo_code_for_tenovi_phi_access')
        elif pseudo_code_for_tenovi_phi_access is None:
            return None

        matching_devices = devices.get_devices_by_pseudo_code(pseudo_code_for_tenovi_phi_access)

        return matching_devices


# Example usage:
if __name__ == "__main__":

    import random
    import sys
    from datetime import datetime

    # -----
    # Generate a new dummy healthie_user_id and create an entry in the user_look_up_codes table

    # Generate a random number and a date stamp
    random_number = random.randint(1000, 9999)
    date_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    healthie_user_id = f"test_{random_number}_{date_stamp}"

    # Initialize LookUpCodesManagement instance
    lookup_manager = LookUpCodesManagement(verbose=True)

    # Test create_entry method
    print(f"Creating entry for healthie_user_id: {healthie_user_id}")
    create_result = lookup_manager.create_entry(healthie_user_id)
    print(f"Create entry result: {create_result}")

    # Test retrieve_entry_by_healthie_user_id method
    if create_result is None:
        print("Failed to create entry")
        lookup_manager.close_connection()
        sys.exit(1)

    print(f"Retrieving entry for healthie_user_id: {healthie_user_id}")
    retrieve_result = lookup_manager.retrieve_entry_by_healthie_user_id(healthie_user_id)
    print(f"Retrieve entry result: {retrieve_result}")

    # Close the database connection
    lookup_manager.close_connection()

    # ---------------
    # Create a new AccountsPairing instance and generate a temporary pseudo code
    pair = AccountsPairing(retrieve_result.get('syntrillo_internal_key'), verbose=True)
    temporary_pseudo_code = pair.create_and_return_unique_temporary_pseudo_code()
    print(f"Temporary pseudo code generated: {temporary_pseudo_code}")

    # ---------------
    # Pair devices using the temporary pseudo code
    print("Please go to the Tenovi dashboard and enter the temporary code in the patient_id field.")
    confirmation = input("Once you have entered the code, please press enter to continue: ")
    if confirmation is not None:
        log = pair.pair_devices_using_temporary_pseudo_code()
        print("Devices paired successfully.")
        pprint(log)

        # list devices paired with the pseudo_code_for_tenovi_phi_access
        matching_devices = pair.get_paired_devices(pseudo_code_for_tenovi_phi_access=retrieve_result.get('pseudo_code_for_tenovi_phi_access'))
        print('Devices paired with the pseudo_code_for_tenovi_phi_access:')
        pprint(matching_devices)

    else:
        print("Pairing process cancelled.")



