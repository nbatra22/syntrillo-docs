from auth import TenoviAuth

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

# Example usage:
if __name__ == "__main__":
    device_properties_module = DeviceProperties(client_domain="syntrillo")

    # Example HWI device ID, replace with a real ID if needed
    hwi_device_id = "0585a82e-3f57-4e0e-a91a-317117c48e11"

    # Get and print properties of a specific device
    device_properties = device_properties_module.get_device_properties(hwi_device_id)
    if device_properties:
        print(f"Properties for device {hwi_device_id}:")
        TenoviAuth.print_pretty_json(device_properties)
