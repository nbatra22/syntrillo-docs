# Path: ./sources/syntrillo/api_tenovi/device_types.py
from syntrillo.api_tenovi.auth import TenoviAuth

class DeviceTypes:
    def __init__(self):
        self.auth = TenoviAuth()

    def get_device_types(self, device_id: str = None):
        """
        Retrieves valid device types for your account.

        These can be used to activate/request new devices via the hwi-devices endpoint using the "name" field. This endpoint can also be used to get static images of devices, or to get the up-front and shipping fees for specific devices.

        https://api2.tenovi.com/hwi-redoc/#operation/hwi-device-types_list

        https://api2.tenovi.com/hwi-redoc/#tag/hwi-device-types/

        return:
            tupple:
              - list: A list of device type dictionaries.
              - dict: The log of the request.
        """
        url = "/hwi/hwi-device-types/"
        if device_id is not None:
            url = f"{url}{device_id}/"
        return self.auth.make_get_request(url)

    @staticmethod
    def print_device_names(device_types):
        """
        Prints the names of all device types.

        Args:
            device_types (list): A list of device type dictionaries.
        """
        for device_type in device_types:
            print(device_type["name"], '|', device_type["id"])

# Example usage:
if __name__ == "__main__":
    device_types_module = DeviceTypes()

    # Get and print device types

    # print all devices
    if True:
        device_types, log = device_types_module.get_device_types()
        print("Device Types:")
        device_types_module.auth.print_pretty_json(device_types)
        print('---------------------')
        device_types_module.auth.print_pretty_json(DeviceTypes.print_device_names(device_types))

    # print a specific device
    if True:
        device_id = "7ffa3c62-cb7b-48e6-8904-f480cf674b1a"
        device_types, log = device_types_module.get_device_types(device_id)
        print('---------------------')
        print("Device Types:")
        device_types_module.auth.print_pretty_json(device_types)




