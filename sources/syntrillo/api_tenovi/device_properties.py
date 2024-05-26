# Path: ./sources/syntrillo/api_tenovi/device_properties.py
from syntrillo.api_tenovi.auth import TenoviAuth

class DeviceProperties:
    def __init__(self, client_domain="syntrillo"):
        self.client_domain = client_domain
        self.auth = TenoviAuth()

    def get_device_properties(self, hwi_device_id):
        """
        Lists all or reads a single Property for a given HWI Device.

        These properties can be used for controlling device-specific settings (e.g. the Step Goals for the Tenovi Watch), or for adding custom, client-defined tags to individual devices (as long as the keys used do not conflict with a pre-defined Tenovi key).

        https://api2.tenovi.com/hwi-redoc/#tag/hwi-device-properties
        """
        url = f"https://api2.tenovi.com/clients/{self.client_domain}/hwi/hwi-devices/{hwi_device_id}/properties/"
        return self.auth.make_get_request(url)

    def create_device_property(self, hwi_device_id, payload):
        """
        Creates a new HWI Device Property with a key-value pair.

        This endpoint can be used to manage any device-specific properties, such as setting the step goal on the Tenovi Watch device. This endpoint can also be used for adding any client-specific properties clients wish to use for internal purposes (for example, to tag devices), as long as the keys used do not conflict with any special use keys described in the Tenovi documentation.

        Note, keys must be unique for a given device. If you try and create a property with an existing key, the existing key-value pair will simply be updated instead.

        https://api2.tenovi.com/hwi-redoc/#tag/hwi-device-properties
        """
        url = f"https://api2.tenovi.com/clients/{self.client_domain}/hwi/hwi-devices/{hwi_device_id}/properties/"
        return self.auth.make_post_request(url, payload)

# Example usage:
if __name__ == "__main__":
    device_properties_module = DeviceProperties()

    # Example HWI device ID, replace with a real ID if needed
    hwi_device_id = "83ca5817-0bb2-4d9c-b131-16eb353ad587"

    # Get and print properties of a specific device
    device_properties = device_properties_module.get_device_properties(hwi_device_id)
    if device_properties:
        print(f"Properties for device {hwi_device_id}:")
        TenoviAuth.print_pretty_json(device_properties)


    if False:
        # Example payload to create a new device property
        payload = {
            "key": "pseudo_code_for_tenovi_phi_access",
            "value": "123456789",
            "synced": False
        }

        # Create a new device property
        new_property_response = device_properties_module.create_device_property(hwi_device_id, payload)
        if new_property_response:
            print("New Property Created:")
            TenoviAuth.print_pretty_json(new_property_response)