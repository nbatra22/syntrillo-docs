from typing import List

from loguru import logger

from syntrillo.api_tenovi.devices import Devices
from syntrillo.api_tenovi.device_measurements import DeviceMeasurements


def find_devices_with_measurements(at_least: int) -> List[str]:
    """
    Returns the list of device_id for which we can get more than `at_least` data
    points with measurements
    """
    all_devices, log = Devices().get_devices()
    if all_devices:
        logger.info(f'Found {len(all_devices)} devices')
    else:
        logger.error('No devices found')
        logger.error(log)

    dm = DeviceMeasurements()
    
    device_ids = []
    for device in all_devices:
        data, _ = dm.get_device_measurements(hwi_device_id=device['id'])
        logger.info(f'Found {len(data)} data points for device {device["id"]}')
        
        if len(data) >= at_least:
            device_ids.append(device['id'])
    
    return device_ids


def my_pprint(x: dict):
    import json
    print(json.dumps(x, indent=4))
