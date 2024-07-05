# Path: ./sources/syntrillo/api_tenovi/device_measurements.py

from syntrillo.api_tenovi.auth import TenoviAuth
from syntrillo.api_tenovi.devices import Devices

class DeviceMeasurements:


    TENOVI_METRICS_BPM_BLOOD_PRESSURE = "blood_pressure"
    TENOVI_METRICS_BPM_PULSE = "pulse"
    TENOVI_METRICS_BPM_IRREGULAR_HEARTBEAT = "irregular_heartbeat"
    TENOVI_METRICS_WATCH_STEPS = "steps"
    TENOVI_METRICS_WATCH_SLEEP = "sleep"
    TENOVI_METRICS_WATCH_HEART_RATE_STATISTICS = "heart_rate_statistics"

    TENOVI_METRICS_PILLBOX_REFILL_INITIATED = "pillbox_refill_initiated"
    TENOVI_METRICS_PILLBOX_REFILLED = "pillbox_refilled"
    TENOVI_METRICS_PILLBOX_OPENED = "pillbox_opened"


    def __init__(self):
        self.auth = TenoviAuth()

    def get_device_measurements(
        self,
        hwi_device_id : str = None,
        created__gte : str = None,
        created__lte : str = None,
        timestamp__gte : str = None,  # zulu time : 2019-08-24T14:15:22Z
        timestamp__lte : str = None,
        metric__name : str = None,
        ):
        """
        Lists all measurement data for a given HWI Device.

        https://api2.tenovi.com/hwi-redoc/#tag/hwi-device-measurements

        Note, the "timestamp" field represents the time the measurement was actually taken, as measured by the device. The "created" field represents the time the measurement was created on our server. For backwards compatibility, the MEASUREMENT Webhook posts the "timestamp" value with both the "timestamp" and "created" key, which may not match the "created" value returned here. Please note the difference between these two fields when filtering via query parameters.

        Args:
            hwi_device_id (str): The HWI Device ID.
            created__gte (str): The earliest server created time to include.
            created__lte (str): The latest server created time to include.
            timestamp__gte (str): The earliest device timestamp to include.
            timestamp__lte (str): The latest device timestamp to include.
            metric__name (str): The metric name to filter by.

        Returns a tupple:
            list: A list of device measurement dictionaries.
            dict: The log of the request.

        """
        url = f"/hwi/hwi-devices/{hwi_device_id}/measurements/"

        # pass only non-None parameters
        params = {k: v for k, v in {
            "created__gte": created__gte,
            "created__lte": created__lte,
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
            measurements, log = device_measurements.get_device_measurements(hwi_device_id)
            print(f"\n-----------\nMeasurements for device {hwi_device_id}:")
            TenoviAuth.print_pretty_json(measurements)

