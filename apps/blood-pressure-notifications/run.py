import os
from typing import List
from loguru import logger

from syntrillo.api_tenovi.device_measurements import DeviceMeasurements
from syntrillo.api_tenovi.devices import Devices

from utils import find_devices_with_measurements, my_pprint

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

def main(
    patient_id: str,
    webhook_data: List[dict] = None,
):
    """
    """
    logger.info("Hello from the blood-pressure-notification service!")

    # get the last blood pressure measurement
    data = [d for d in webhook_data if d['metric_name_read_only'] == 'blood_pressure']
    if not data:
        logger.info(f'No blood pressure measurements found for patient_id {patient_id}')
        return
    
    last_measurement = data[-1]
    device_id = last_measurement['hardware_uuid']
    timestamp = last_measurement['timestamp']

    logger.info(f'Received blood pressure measurement for device {device_id} and patient {patient_id} taken at {timestamp}')
    
    # get blood pressure measurements for this device for the last 24 hours
    # TODO
    
    # add moving averages, trends and other metrics
    # TODO

    # compute alert metrics
    # TODO

    # send notifications to Healthie API
    # TODO

    # push data to Elasticsearch for real-time visualizations
    # TODO


    logger.info(f'Getting blood pressure measurements for {len(device_ids)} devices')
    blood_pressure = {}
    for device_id in device_ids:
        data, _ = DeviceMeasurements().get_device_measurements(
            hwi_device_id=device_id,
            metric__name='blood_pressure',
        )
        blood_pressure[device_id] = data
        logger.info(f'Found {len(data)} blood pressure measurements for device {device_id}')
    
        blood_measurements = BloodPressureMeasurements(
            device_id=device_id,
            measurements=data,
        )

    # pprint(measurments)

    # Get device with at least 10 data points
    # device_ids = find_devices_with_measurements(at_least=10)
    device_ids = [os.environ['SAMPLE_DEVICE_ID']]

    data, log = DeviceMeasurements().get_device_measurements(hwi_device_id=device_ids[0])
    logger.info(f'Data: {data}')
    logger.info(log)

if __name__ == "__main__":
    
    # sample webhook data
    # TODO: the exact shape of the data is not known, until we create an AWS lambda function
    # expose it behind API Gateway, and add it as webhook in the Tenovi API
    # In the meantime, we use this sample data.
    webhook_data = [
        {
            "value": "85.00",
            "secondary_value": "0.00",
            "hardware_uuid": "27E1F4126AE5",
            "created": "2024-12-15T17:27:27.474295Z",
            "timestamp": "2024-12-15T17:27:00.000000Z",
            "timezone_offset": -5,
            "metric_name_read_only": "pulse",
            "device_name": "Tenovi BPM - L",
            "anomalous_timestamp": False,
            "filter_params": {
                "measurement_index": 3165
            },
            "webhook_responses": None
        },
        {
            "value": "128.00",
            "secondary_value": "74.00",
            "hardware_uuid": "27E1F4126AE5",
            "created": "2024-12-15T17:27:27.443140Z",
            "timestamp": "2024-12-15T17:27:00.000000Z",
            "timezone_offset": -5,
            "metric_name_read_only": "blood_pressure",
            "device_name": "Tenovi BPM - L",
            "anomalous_timestamp": False,
            "filter_params": {
                "measurement_index": 3165
            },
            "webhook_responses": None
        }
    ]
    main(
        patient_id='5391367',
        webhook_data=webhook_data,
    )
