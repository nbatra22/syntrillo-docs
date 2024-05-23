from auth import TenoviAuth

class DeviceTypes:
    def __init__(self, client_domain="syntrillo"):
        self.client_domain = client_domain
        self.auth = TenoviAuth()

    def get_device_types(self):
        """
        Retrieves valid device types for your account.

        These can be used to activate/request new devices via the hwi-devices endpoint using the "name" field. This endpoint can also be used to get static images of devices, or to get the up-front and shipping fees for specific devices.

        https://api2.tenovi.com/hwi-redoc/#tag/hwi-device-types
        """
        url = f"https://api2.tenovi.com/clients/{self.client_domain}/hwi/hwi-device-types/"
        return self.auth.make_get_request(url)


# Example usage:
if __name__ == "__main__":
    device_types_module = DeviceTypes(client_domain="syntrillo")

    # Get and print device types
    device_types = device_types_module.get_device_types()
    if device_types:
        print("Device Types:")
        device_types_module.auth.print_pretty_json(device_types)




