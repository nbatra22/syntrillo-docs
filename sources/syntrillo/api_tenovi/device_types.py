# Path: ./sources/syntrillo/api_tenovi/device_types.py

from typing import Tuple

from syntrillo.api_tenovi.auth import TenoviAuth

class DeviceTypes:
    """
    The DeviceTypes class is used to retrieve valid device types for your account.
    """

    # Device names
    TENOVI_DEVICE_NAME__WATCH = "Tenovi Watch"
    TENOVI_DEVICE_NAME__PILLBOX = "Tenovi Pillbox"
    TENOVI_DEVICE_NAME__BPM_PREFIX = "Tenovi BPM"
    TENOVI_DEVICE_NAME__BPM_LARGE  = "Tenovi BPM - L"
    TENOVI_DEVICE_NAME__BPM_SMALL  = "Tenovi BPM - S"
    TENOVI_DEVICE_NAME__BPM_OMRON  = "Omron BPM"

    SYNTRILLO_TENOVI_DEVICE_NAMES = [
        TENOVI_DEVICE_NAME__WATCH,
        TENOVI_DEVICE_NAME__PILLBOX,
        TENOVI_DEVICE_NAME__BPM_PREFIX,
        TENOVI_DEVICE_NAME__BPM_LARGE,
        TENOVI_DEVICE_NAME__BPM_SMALL,
        TENOVI_DEVICE_NAME__BPM_OMRON,
    ]

    def __init__(self):
        self.auth = TenoviAuth()

    def get_device_types(self) -> Tuple[list, dict]:
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

        return self.auth.make_get_request(url)

    def print_device_names(self, device_types, print_all=False):
        """
        Prints the names of all device types.

        Args:
            device_types (list): A list of device type dictionaries.
        """
        for device_type in device_types:
            if print_all or device_type["name"] in DeviceTypes.SYNTRILLO_TENOVI_DEVICE_NAMES:
                print(device_type["name"].ljust(20), device_type["id"])

# Example usage:
if __name__ == "__main__":
    device_types_module = DeviceTypes()

    # Get and print device types

    # print our devices
    device_types, log = device_types_module.get_device_types()
    print(log)
    if log['success']:
        device_types_module.print_device_names(device_types)
