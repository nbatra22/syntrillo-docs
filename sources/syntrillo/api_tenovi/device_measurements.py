# Path: ./sources/syntrillo/api_tenovi/device_measurements.py

from syntrillo.api_tenovi.auth import TenoviAuth

class DeviceMeasurements:
    def __init__(self, client_domain="syntrillo"):
        self.client_domain = client_domain
        self.auth = TenoviAuth()

    def get_device_measurements(self, hwi_device_id : str):
        """
        Lists all measurement data for a given HWI Device.

        https://api2.tenovi.com/hwi-redoc/#tag/hwi-device-measurements
        """
        url = f"https://api2.tenovi.com/clients/{self.client_domain}/hwi/hwi-devices/{hwi_device_id}/measurements/"
        return self.auth.make_get_request(url)

# Example usage:
if __name__ == "__main__":
    device_measurements_module = DeviceMeasurements()

    # Example HWI device ID, replace with a real ID if needed
    # hwi_device_id = "83ca5817-0bb2-4d9c-b131-16eb353ad587"
    # hwi_device_id = "3399fda7-121d-42bd-931b-3389a09567c1"  # Omar Migo Clip
    hwi_device_id = "beb8e7cc-e8fe-4c8c-a273-bc54ac4bf9f1"  # Demo Patient - Tenovi Pulse Ox

    # Get and print measurements of a specific device
    device_measurements = device_measurements_module.get_device_measurements(hwi_device_id)
    if device_measurements:
        print(f"Measurements for device {hwi_device_id}:")
        TenoviAuth.print_pretty_json(device_measurements)

