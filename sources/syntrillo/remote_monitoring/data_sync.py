
import json
import uuid
from datetime import datetime, timedelta

from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.api_tenovi.devices import Devices
from syntrillo.api_tenovi.device_measurements import DeviceMeasurements
from syntrillo.api_healthie.metrics import HealthieMetrics

class RemoteMonitoringDataSync:

    def __init__(
        self,
        syntrillo_internal_key : uuid.UUID,
        ) -> None:
        """
        For a given patient, synchronize data:
        - from the Tenovi to our PHI database
        - from out PHI database to Healthie

        Args:
            syntrillo_internal_key (uuid.UUID): The syntrillo internal key (UUID).

        """

        # ---------------
        # get user lookup codes
        lookup_codes = LookUpCodesManagement()
        entry = lookup_codes.retrieve_entry_by_internal_key(syntrillo_internal_key)

        self.pseudo_code_for_tenovi_phi_access = entry['pseudo_code_for_tenovi_phi_access']
        self.healthie_user_id = entry['healthie_user_id']
        self.syntrillo_internal_key = syntrillo_internal_key

        # ---------------
        # get devices for this user
        devices = Devices()
        self.user_devices, log = devices.get_devices_by_pseudo_code(self.pseudo_code_for_tenovi_phi_access)

        # ---------------
        # set up database connection for this user
        self.syntrillo_database_manager = SyntrilloDatabaseManager(syntrillo_internal_key)

        # ---------------
        # instantiate Tenovi device measurements class
        self.device_measurements = DeviceMeasurements()

        # ---------------
        # instantiate Healthie API metrics class
        self.healthie_metrics = HealthieMetrics()

        """ user devices:
            {
            "id": "ff7ddf32-1472-450e-89ae-362416765d8b",
            "status": "Connected",
            "device": {
                "id": "54fd3ddb-bf1a-49a6-a1f5-266b99b805b3",
                "fulfillment_request": null,
                "created": "2024-06-13T18:28:53.798175Z",
                "name": "Tenovi BPM - L",
                "hardware_uuid": "FB5E23D5E7F7",

        """

        """ measurements:
            {
                "created": "2024-06-21T15:47:45.248142Z",
                "device_name": "Tenovi BPM - L",
                "estimated_timestamp": false,
                "filter_params": {
                    "measurement_index": 190
                },
                "hardware_uuid": "FB5E23D5E7F7",
                "hwi_device_id": "ff7ddf32-1472-450e-89ae-362416765d8b",
                "metric": "pulse",
                "patient_id": "Omar Real Device",
                "sensor_code": "10",
                "timestamp": "2024-06-21T15:47:00.000000Z",
                "timezone_offset": -4,
                "value_1": "72.00",
                "value_2": "0.00"
            }
        """

        """ storage format in Syntrillo database
        data_type = "tenovi_raw_bpm" / "tenovi_raw_pillbox" / "tenovi_raw_watch"
        data =
        {
            "device_name": "Tenovi BPM - L",
            "hwi_device_id": "ff7ddf32-1472-450e-89ae-362416765d8b",
            "timestamp": "2024-06-21T15:47:00.000000Z",
            "timezone_offset": -4,
            "metric": "pulse",
            "value_1": "72.00",
            "value_2": "0.00"
        }

        """

    def sync_tenovi_to_syntrillo(self):
        """
        Sync data from Tenovi to Syntrillo PHI database.
        """
        overall_log = {
            "success": True,
            "number_of_records_inserted": 0,
            "logs": []
        }

        # Loop over devices
        for device in self.user_devices:
            # Get latest timestamp for this device
            latest_record, log = self.syntrillo_database_manager.get_latest_record_for_tenovi_device(device['device']['name'])
            if not log["success"]:
                overall_log["logs"].append(log)
                overall_log["success"] = False
                continue

            # adding a tiny amount of time to the latest timestamp to avoid duplicates (since it is greater than or equal to)
            latest_timestamp_zulu_updated_str = None
            if latest_record:
                latest_timestamp_zulu_updated = datetime.strptime(latest_record['timestamp_zulu'], "%Y-%m-%dT%H:%M:%S.%fZ")
                latest_timestamp_zulu_updated += timedelta(microseconds=1)
                latest_timestamp_zulu_updated_str = latest_timestamp_zulu_updated.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            # Get data from Tenovi device measurements class
            measurements, log = self.device_measurements.get_device_measurements(
                hwi_device_id=device['id'],
                timestamp__gte=latest_timestamp_zulu_updated_str,
            )
            if not log["success"]:
                overall_log["logs"].append(log)
                overall_log["success"] = False
                continue

            # Loop over measurements
            for measurement in measurements:
                # Insert into Syntrillo database
                log = self.syntrillo_database_manager.insert_tenovi_raw_measurement(
                    device_name=measurement['device_name'],
                    timestamp_zulu=measurement['timestamp'],
                    data_json=json.dumps(measurement),
                    metric_name=measurement['metric'],
                    value_1=measurement['value_1'],
                    value_2=measurement['value_2']
                )
                if not log["success"]:
                    overall_log["logs"].append(log)
                    overall_log["success"] = False
                else:
                    overall_log["number_of_records_inserted"] += 1

        return overall_log


    def sync_syntrillo_to_healthie(self):
        """
        Sync data from Syntrillo PHI database to Healthie.
        """
        overall_log = {
            "success": True,
            "number_of_records_inserted": 0,
            "lastest_timestamp": None,
            "logs": []
        }

        # -------------------
        # Blood pressure

        # get latest timestamp from Healthie
        latest_timestamp = self.healthie_metrics.get_metric_latest_timestamp(
            self.healthie_user_id,
            HealthieMetrics.HEALTHIE_METRICS_BLOOD_PRESSURE_CATEGORY
        )

        overall_log["lastest_timestamp"] = latest_timestamp

        # get all records from syntrillo database for this category after the latest timestamp
        records, log = self.syntrillo_database_manager.get_blood_pressure_records_after_timestamp(latest_timestamp)

        # loop over records, and store using Healthie API store_blood_pressure_data
        for record in records:
            response, log = self.healthie_metrics.store_blood_pressure_data(
                self.healthie_user_id,
                created_at=datetime.strptime(record['timestamp_zulu'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                systolic=record['value_1'],
                diastolic=record['value_2'],
            )
            if not log["success"]:
                overall_log["logs"].append(log)
                overall_log["success"] = False
            else:
                overall_log["number_of_records_inserted"] += 1

        # -------------------
        return overall_log



if __name__ == '__main__':

    lookup_codes = LookUpCodesManagement()
    entry = lookup_codes.retrieve_entry_by_healthie_user_id('1051529') # 1051529 : Omar's "Patient One"

    sync = RemoteMonitoringDataSync(entry['syntrillo_internal_key'])

    if False:
        print(sync.healthie_user_id)
        print(sync.pseudo_code_for_tenovi_phi_access)
        print(sync.syntrillo_internal_key)

        # Pretty print user devices
        print(json.dumps(sync.user_devices, indent=4))

    if False:
        overall_log = sync.sync_tenovi_to_syntrillo()

        print(json.dumps(overall_log, indent=4))

    if True:
        overall_log = sync.sync_syntrillo_to_healthie()

        print(json.dumps(overall_log, indent=4))



