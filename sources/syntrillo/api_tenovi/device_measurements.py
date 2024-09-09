# Path: ./sources/syntrillo/api_tenovi/device_measurements.py

from datetime import datetime, timezone, timedelta

from syntrillo.api_tenovi.auth import TenoviAuth
from syntrillo.api_tenovi.devices import Devices

from syntrillo.system.logger import logger

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
        timeout : int = None,
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

        response, log = self.auth.make_get_request(
            url,
            params=params,
            timeout=timeout
        )

        return response, log


    def get_device_measurements_created_window_504_adaptive(
        self,
        hwi_device_id: str,
        created__gte: str,
        created__lte: str,
        timeout: int = 10,
        smallest_window_days: int = 7,
        recurvisely: bool = False,
        recursive_level: int = 0
    ):
        """
        Try to get the measurements for a given device and created window,
        but if the request times out, retry with a smaller window until it succeeds
        and aggregate the results.

        Args:
            hwi_device_id (str): The HWI Device ID.
            created__gte (str): The earliest server created time to include.
            created__lte (str): The latest server created time to include.
            timeout (int): The timeout in seconds.

        Returns:
            tuple (list, dict): A tuple where
                - the first element is a list of device measurement dictionaries,
                - the second element is the log of the request.
        """

        # if called recurvisely and window is too small, return an empty list
        if recurvisely and \
            (datetime.strptime(created__lte, "%Y-%m-%dT%H:%M:%S.%fZ")
            - datetime.strptime(created__gte, "%Y-%m-%dT%H:%M:%S.%fZ")) < timedelta(days=smallest_window_days):

            log = {
                'success': False,
                'partial_success': False,
                'status_code': None,
                'message': 'Window too small.'
                }

            return [], log

        # Try to get the measurements for the given window
        measurements, log = self.get_device_measurements(
            hwi_device_id=hwi_device_id,
            created__gte=created__gte,
            created__lte=created__lte,
            timeout=timeout
        )

        log['partial_success'] = log['success']

        # If the request timed out, retry with a smaller window
        if log['success'] is False and log['status_code'] == 504:

            # AWS logger
            if recursive_level == 0:
                logger.warning(f"504 errors. Attempting to aggregate results with smaller time frames. Gaps may exist. Device ID: {hwi_device_id}")

            # Convert datetime strings to datetime objects
            created__gte_dt = datetime.strptime(created__gte, "%Y-%m-%dT%H:%M:%S.%fZ")
            created__lte_dt = datetime.strptime(created__lte, "%Y-%m-%dT%H:%M:%S.%fZ")

            # Calculate the midpoint
            created__mid_dt = created__gte_dt + (created__lte_dt - created__gte_dt) / 2

            # Convert the datetime object back to string
            created__mid = created__mid_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            # Get the measurements for the first half
            measurements1, log1 = self.get_device_measurements_created_window_504_adaptive(
                hwi_device_id=hwi_device_id,
                created__gte=created__gte,
                created__lte=created__mid,
                timeout=timeout,
                recurvisely=True,
                recursive_level=recursive_level + 1
            )
            # Get the measurements for the second half
            measurements2, log2 = self.get_device_measurements_created_window_504_adaptive(
                hwi_device_id=hwi_device_id,
                created__gte=created__mid,
                created__lte=created__lte,
                timeout=timeout,
                recurvisely=True,
                recursive_level=recursive_level + 1
            )
            # Aggregate the results
            measurements = measurements1 + measurements2

            # log
            log = {
                'success': False,
                'partial_success': log1['success'] or log2['success'],
                'message': '504 errors. Attempted to aggregate results with smaller time frames. Gaps may exist.'
            }


        if measurements is not None:
            if len(measurements) > 0:
                # sort the measurements by created time
                measurements = sorted(measurements, key=lambda x: x['created'])
                # log
                log['partial_success'] = True

        return measurements, log



# Example usage:
if __name__ == "__main__":

    # Omar new devices
    if False:
        device_measurements = DeviceMeasurements()
        device_ids = [
                   # "e154d35e-4543-4c15-abdd-cbdc8f482654",  # Omar New - HWI - Watch
                   "55fc9fab-3a74-4d61-b949-c1f08ea76f2b",  # Omar New - HWI - Pillbox
                   # "ff7ddf32-1472-450e-89ae-362416765d8b"  # Omar New - HWI - BPM
                   ]

        # Get and print all devices or a specific device
        for hwi_device_id in device_ids:

            devices = Devices()
            device = devices.get_devices(hwi_device_id=hwi_device_id)

            created__gte = device[0]['device']['created']
            # created__lte = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            # created__lte is created__gte + 1 day
            created__lte = (datetime.strptime(created__gte, "%Y-%m-%dT%H:%M:%S.%fZ")
                            + timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            measurements, log = device_measurements.get_device_measurements(
                hwi_device_id=hwi_device_id,
                created__gte=created__gte,
                # created__lte="2024-02-08T00:00:00.000000Z",
                created__lte=created__lte,
                timeout=10,
                )
            print(f"\n-----------\nDevice {hwi_device_id}:")
            TenoviAuth.print_pretty_json(log)
            # TenoviAuth.print_pretty_json(measurements)
            # print number of measurements
            if log['success']:
                print(f"Number of measurements: {len(measurements)}")
                # print first measurement
                if measurements and len(measurements) > 0 and False:
                    print("First measurement:")
                    TenoviAuth.print_pretty_json(measurements[0])


    if True:
        device_measurements = DeviceMeasurements()
        device_ids = [
                   "e154d35e-4543-4c15-abdd-cbdc8f482654",  # Omar New - HWI - Watch
                   "55fc9fab-3a74-4d61-b949-c1f08ea76f2b",  # Omar New - HWI - Pillbox
                   "ff7ddf32-1472-450e-89ae-362416765d8b"  # Omar New - HWI - BPM
                   ]

        # Get and print all devices or a specific device
        for hwi_device_id in device_ids:

            devices = Devices()
            device = devices.get_devices(hwi_device_id=hwi_device_id)

            created__gte = device[0]['device']['created']
            created__lte = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            measurements, log = device_measurements.get_device_measurements_created_window_504_adaptive(
                hwi_device_id=hwi_device_id,
                created__gte=created__gte,
                created__lte=created__lte,
                timeout=10,
                )
            print(f"\n-----------\nDevice {hwi_device_id}:")
            TenoviAuth.print_pretty_json(log)
            # TenoviAuth.print_pretty_json(measurements)
            # print number of measurements
            if measurements :
                print(f"Number of measurements: {len(measurements)}")


