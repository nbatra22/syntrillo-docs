# Path: ./sources/syntrillo/api_tenovi/device_properties.py

from syntrillo.api_tenovi.auth import TenoviAuth

class DeviceProperties:
    """

    Class used to set and get the 'pseudo_code_for_tenovi_phi_access' device property.

    From https://api2.tenovi.com/hwi-redoc/#tag/hwi-device-properties :

    'These properties can be used for controlling device-specific settings (e.g. the Step Goals for the Tenovi Watch), or for adding custom, client-defined tags to individual devices (as long as the keys used do not conflict with a pre-defined Tenovi key). See https://tenovi.com/api-docs for a list of device-specific Properties.

    For device-specific settings, the "synced" field can be used to check if the setting has been successfully applied to the device or not. Note, syncing often requires the device to connect to our network, which, for some devices, only occurs when a measurement is taken).'


    """
    def __init__(self):
        self.auth = TenoviAuth()

    def get_device_properties(self, hwi_device_id : str):
        """
        Lists all or reads a single Property for a given HWI Device.

        Arg:
            hwi_device_id (str): The HWI Device ID.

        Returns a tupple:
            list: A list of device property dictionaries.
            dict: The log of the request.
        """
        url = f"/hwi/hwi-devices/{hwi_device_id}/properties/"
        return self.auth.make_get_request(url)

    def create_device_property(self, hwi_device_id : str, payload : dict):
        """
        Creates a new HWI Device Property with a key-value pair.

        from https://api2.tenovi.com/hwi-redoc/#operation/hwi-devices_properties_create :

        'Note, keys must be unique for a given device. If you try and create a property with an existing key, the existing key-value pair will simply be updated instead.'

        Args:
            hwi_device_id (str): The HWI Device ID.
            payload (dict): The key-value pair to create.

        Returns a tupple:
            dict: The created device property dictionary.
            dict: The log of the request.
        """
        url = f"/hwi/hwi-devices/{hwi_device_id}/properties/"
        return self.auth.make_post_request(url, payload)

    def create__pseudo_code_for_tenovi_phi_access__property(self, hwi_device_id : str, pseudo_code : str):
        """
        Creates a new HWI Device Property with the key 'pseudo_code_for_tenovi_phi_access' and the given pseudo_code value.

        Args:
            hwi_device_id (str): The HWI Device ID.
            pseudo_code (str): The pseudo code to set.

        Returns a tupple:
            dict: The created device property dictionary.
            dict: The log of the request.
        """
        payload = {
            "key": "pseudo_code_for_tenovi_phi_access",
            "value": pseudo_code,
            "synced": False
        }
        return self.create_device_property(hwi_device_id, payload)

    def create__healthie_user_id__property(self, hwi_device_id : str, healthie_user_id : str):
        """
        Creates a new HWI Device Property with the key 'healthie_user_id' and the given healthie_user_id value.

        Args:
            hwi_device_id (str): The HWI Device ID.
            healthie_user_id (str): The healthie user ID to set.

        Returns a tupple:
            dict: The created device property dictionary.
            dict: The log of the request.
        """
        payload = {
            "key": "healthie_user_id",
            "value": healthie_user_id,
            "synced": False
        }
        return self.create_device_property(hwi_device_id, payload)

# Example usage:
if __name__ == "__main__":
    device_properties_module = DeviceProperties()

    # hwi_device_id = "e154d35e-4543-4c15-abdd-cbdc8f482654"  # Omar Watch
    hwi_device_id = "6d92777f-8ef3-463d-b8e2-d5fcb7d303ec"  # test watch

    # Get and print properties of a specific device
    device_properties, log = device_properties_module.get_device_properties(hwi_device_id)
    if device_properties:
        print(f"Properties for device {hwi_device_id}:")
        TenoviAuth.print_pretty_json(device_properties)
    else:
        print(f"No properties found for device {hwi_device_id}.")
        print(log)


    if False:
        # Example payload to create a new device property
        payload = {
            "key": "pseudo_code_for_tenovi_phi_access",
            "value": "123456789",
            "synced": False
        }

        # Create a new device property
        new_property_response, log = device_properties_module.create_device_property(hwi_device_id, payload)
        if new_property_response:
            print("New Property Created:")
            TenoviAuth.print_pretty_json(new_property_response)