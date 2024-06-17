# Path: ./sources/syntrillo/api_tenovi/device_measurements.py

from syntrillo.api_tenovi.auth import TenoviAuth
from devices import Devices

class DeviceMeasurements:
    def __init__(self):
        self.auth = TenoviAuth()

    def get_devices_by_pseudo_code(self, pseudo_code_for_tenovi_phi_access):
        self.pseudo_code_for_tenovi_phi_access = pseudo_code_for_tenovi_phi_access
        # get devices for this user
        if pseudo_code_for_tenovi_phi_access is not None:
            devices_module = Devices()
            self.user_devices = devices_module.get_devices_by_pseudo_code(pseudo_code_for_tenovi_phi_access)
        else:
            self.user_devices = None

    def get_devices_by_patient_external_id(self, external_id):
        self.external_id = external_id
        # get devices for this user
        if external_id is not None:
            devices_module = Devices()
            self.user_devices = devices_module.get_devices_by_patient_external_id(external_id)
        else:
            self.user_devices = None


    def _get_device_measurements(
        self,
        hwi_device_id : str = None,
        timestamp__gte : str = None,  # zulu time : 2019-08-24T14:15:22Z
        timestamp__lte : str = None,
        metric__name : str = None,
        ):
        """
        Lists all measurement data for a given HWI Device.

        https://api2.tenovi.com/hwi-redoc/#tag/hwi-device-measurements

        Args:
            hwi_device_id (str): The HWI Device ID.
            timestamp__gte (str): The earliest timestamp to include.
            timestamp__lte (str): The latest timestamp to include.
            metric__name (str): The metric name to filter by.

        Returns a tupple:
            list: A list of device measurement dictionaries.
            dict: The log of the request.

        """
        url = f"/hwi/hwi-devices/{hwi_device_id}/measurements/"

        # pass only non-None parameters
        params = {k: v for k, v in {
            "timestamp__gte": timestamp__gte,
            "timestamp__lte": timestamp__lte,
            "metric__name": metric__name
        }.items() if v is not None}

        return self.auth.make_get_request(
            url,
            params=params
        )





# Example usage:
if __name__ == "__main__":

    # Omar new devices
    if True:
        device_measurements = DeviceMeasurements()
        device_ids = [
                   "e154d35e-4543-4c15-abdd-cbdc8f482654",  # Omar New - HWI - Watch
                   "55fc9fab-3a74-4d61-b949-c1f08ea76f2b",  # Omar New - HWI - Pillbox
                   "ff7ddf32-1472-450e-89ae-362416765d8b"  # Omar New - HWI - BPM
                   ]

        # Get and print all devices or a specific device
        for hwi_device_id in device_ids:
            measurements, log = device_measurements._get_device_measurements(hwi_device_id)
            print(f"\n-----------\nMeasurements for device {hwi_device_id}:")
            TenoviAuth.print_pretty_json(measurements)

