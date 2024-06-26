# Path: ./sources/syntrillo/remote_monitoring/dummy_data_generator.py

import uuid
from datetime import datetime, timedelta, timezone
import random
import json
import pymysql

from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.api_tenovi.devices import Devices
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager

class TenoviDummyDataGenerator:
    """
    Generate dummy Tenovi devices data for a given patient
    """

    def __init__(self, syntrillo_internal_key: uuid.UUID, verbose: bool = False):
        """
        Initialize the data generator with necessary details
        """
        # get id entry
        lookup_codes_management = LookUpCodesManagement()
        entry = lookup_codes_management.retrieve_entry_by_internal_key(syntrillo_internal_key)

        self.syntrillo_internal_key = syntrillo_internal_key
        self.healthie_user_id = entry["healthie_user_id"]
        self.pseudo_code_for_tenovi_phi_access = entry["pseudo_code_for_tenovi_phi_access"]

        # database manager
        self.syntrillo_database_manager = SyntrilloDatabaseManager(syntrillo_internal_key=syntrillo_internal_key)

        # get devices id
        devices_api = Devices()
        devices, log = devices_api.get_devices_by_pseudo_code(self.pseudo_code_for_tenovi_phi_access)

        for device in devices:
            if device['device']['name'] == "Tenovi BPM - L":
                self.device_id_BMP = device["id"]
            elif device['device']['name'] == "Tenovi Pillbox":
                self.device_id_pillbox = device["id"]
            elif device['device']['name'] == "Tenovi Watch":
                self.device_id_watch = device["id"]

        if verbose:
            print(f"TenoviDummyDataGenerator: {self.healthie_user_id} - {self.syntrillo_internal_key} - {self.pseudo_code_for_tenovi_phi_access}")
            print(f"TenoviDummyDataGenerator: {self.device_id_BMP} - {self.device_id_pillbox} - {self.device_id_watch}")

    def set_patient_state(
        self,
        patient_state_blood_pressure: str,
        patient_state_heart_rate: str,
        patient_state_steps: str
        ):
        """
        Set the patient state to generate the data accordingly
        """
        self.patient_state_blood_pressure = patient_state_blood_pressure

        if patient_state_blood_pressure == "healthy":
            self.systolic_min = 90
            self.systolic_max = 120
            self.systolic_mean = 105
            self.systolic_var = 5
            self.diastolic_min = 60
            self.diastolic_max = 80
            self.diastolic_mean = 70
            self.diastolic_var = 5
        elif patient_state_blood_pressure == "hypertensive":
            self.systolic_min = 140
            self.systolic_max = 180
            self.systolic_mean = 160
            self.systolic_var = 5
            self.diastolic_min = 90
            self.diastolic_max = 120
            self.diastolic_mean = 100
            self.diastolic_var = 5
        elif patient_state_blood_pressure == "hypotensive":
            self.systolic_min = 90
            self.systolic_max = 120
            self.systolic_mean = 105
            self.systolic_var = 5
            self.diastolic_min = 60
            self.diastolic_max = 80
            self.diastolic_mean = 70
            self.diastolic_var = 5

        if patient_state_heart_rate == "healthy":
            self.pulse_min = 60
            self.pulse_max = 100
            self.pulse_mean = 80
            self.pulse_var = 5
        elif patient_state_heart_rate == "tachycardic":
            self.pulse_min = 100
            self.pulse_max = 120
            self.pulse_mean = 110
            self.pulse_var = 5
        elif patient_state_heart_rate == "bradycardic":
            self.pulse_min = 40
            self.pulse_max = 60
            self.pulse_mean = 50
            self.pulse_var = 5


        if patient_state_steps == "healthy":
            self.steps_min = 5000
            self.steps_max = 10000
            self.steps_mean = 7500
            self.steps_var = 5
        elif patient_state_steps == "sedentary":
            self.steps_min = 1000
            self.steps_max = 5000
            self.steps_mean = 3000
            self.steps_var = 5
        elif patient_state_steps == "active":
            self.steps_min = 10000
            self.steps_max = 15000
            self.steps_mean = 12500
            self.steps_var = 5


    def generate_BMP_data_point(self):
        """
        Generate a single blood pressure measurement data point
        """
        systolic = random.gauss(self.systolic_mean, self.systolic_var)
        diastolic = random.gauss(self.diastolic_mean, self.diastolic_var)
        pulse = random.gauss(self.pulse_mean, self.pulse_var)

        systolic = round(max(self.systolic_min, min(systolic, self.systolic_max)), 0)
        diastolic = round(max(self.diastolic_min, min(diastolic, self.diastolic_max)), 0)
        pulse = round(max(self.pulse_min, min(pulse, self.pulse_max)), 0)

        return systolic, diastolic, pulse

    def generate_BMP_device_data(self, date_start: datetime, date_end: datetime):
        """
        Generate blood pressure data for the given date range.
        """
        date = date_start
        i = 0

        while date < date_end:
            i += 1
            if random.random() > 0.1:
                date += timedelta(days=1)

            systolic, diastolic, pulse = self.generate_BMP_data_point()
            timestamp = date + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
            created = timestamp + timedelta(minutes=random.randint(0, 59))

            value1_str = f"{systolic:.2f}"
            value2_str = f"{diastolic:.2f}"
            created_str = created.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            timestamp_zulu = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            # ----------------------
            # blood pressure data
            data_bp = {
                "metric": "blood_pressure",
                "created": created_str,
                "value_1": value1_str,
                "value_2": value2_str,
                "timestamp": timestamp_zulu,
                "patient_id": self.healthie_user_id,
                "device_name": "Tenovi BPM - L",
                "sensor_code": "10",
                "filter_params": {
                    "measurement_index": 100 + i
                },
                "hardware_uuid": "FB5E23D5E7F7",
                "hwi_device_id": self.device_id_BMP,
                "timezone_offset": -4,
                "estimated_timestamp": False,
                "dummy_data": True
            }

            self.syntrillo_database_manager.insert_tenovi_raw_measurement(
                device_name="Tenovi BPM - L",
                metric_name="blood_pressure",
                value_1=value1_str,
                value_2=value2_str,
                timestamp_zulu=timestamp_zulu,
                timezone_offset=-4,
                data_json=json.dumps(data_bp, default=str)
            )

            # ----------------------
            # pulse data
            value1_str = f"{pulse:.2f}"

            data_hr = {
                "metric": "pulse",
                "created": created_str,
                "value_1": value1_str,
                "value_2": "0.00",
                "timestamp": timestamp_zulu,
                "patient_id": "Omar Real Device",
                "device_name": "Tenovi BPM - L",
                "sensor_code": "10",
                "filter_params": {"measurement_index": 200+i},
                "hardware_uuid": "FB5E23D5E7F7",
                "hwi_device_id": self.device_id_BMP,
                "timezone_offset": -4,
                "estimated_timestamp": False,
                "dummy_data": True
                }

            self.syntrillo_database_manager.insert_tenovi_raw_measurement(
                device_name="Tenovi BPM - L",
                metric_name="pulse",
                value_1=value1_str,
                value_2="0.00",
                timestamp_zulu=timestamp_zulu,
                timezone_offset=-4,
                data_json=json.dumps(data_hr, default=str)
            )

        return None

    def generate_watch_data_point(self, timestamp: datetime):

        # ----------------------
        # heart rate

        # take a sample of 3600 heart rate values
        heart_rate_values = [random.gauss(self.pulse_mean, self.pulse_var) for _ in range(3600)]
        # get the average and max heart rate
        heart_rate_average = round(sum(heart_rate_values) / len(heart_rate_values), 0)
        heart_rate_max = round(max(heart_rate_values), 0)

        # ----------------------
        # steps
        # the patient walks only if between 8am and 6pm
        if timestamp.hour >= 8 and timestamp.hour < 18:
            steps = random.gauss(self.steps_mean, self.steps_var)
            steps = round(max(self.steps_min, min(steps, self.steps_max)), 0)
        else:
            steps = 0

        return heart_rate_average, heart_rate_max, steps


    def generate_watch_device_data(self, date_start: datetime, date_end: datetime):
        """
        Generate hourly watch data for the given date range.
        """
        date = date_start
        i = 0

        while date < date_end:
            i += 1
            date += timedelta(hours=1)

            timestamp = date + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
            created = timestamp + timedelta(minutes=random.randint(0, 59))

            created_str = created.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            timestamp_zulu = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            heart_rate_average, heart_rate_max, steps = self.generate_watch_data_point(timestamp)

            # ----------------------
            # HR stats
            value1_str = f"{heart_rate_average:.2f}"
            value2_str = f"{heart_rate_max:.2f}"

            data_hr_stats = {
                "metric": "heart_rate_statistics",
                "created": created_str,
                "value_1": value1_str,
                "value_2": value2_str,
                "timestamp": timestamp_zulu,
                "patient_id": self.healthie_user_id,
                "device_name": "Tenovi Watch",
                "sensor_code": "15",
                "filter_params": {"period": 60, "wearable_code": 0, "max_heart_rate": 91, "min_heart_rate": 0, "average_heart_rate": 80},
                "hardware_uuid": "FB5E23D5E7F7",
                "hwi_device_id": self.device_id_watch,
                "timezone_offset": -4,
                "estimated_timestamp": False,
                "dummy_data": True
                }

            self.syntrillo_database_manager.insert_tenovi_raw_measurement(
                device_name="Tenovi Watch",
                metric_name="heart_rate_statistics",
                value_1=value1_str,
                value_2=value2_str,
                timestamp_zulu=timestamp_zulu,
                timezone_offset=-4,
                data_json=json.dumps(data_hr_stats, default=str)
            )

            # ----------------------
            # steps
            value1_str = f"{steps:.2f}"

            data_steps = {
                "metric": "steps",
                "created": created_str,
                "value_1": value1_str,
                "value_2": "0.00",
                "timestamp": timestamp_zulu,
                "patient_id": self.healthie_user_id,
                "device_name": "Tenovi Watch",
                "sensor_code": "15",
                "filter_params": {"wearable_code": 0},
                "hardware_uuid": "FB5E23D5E7F7",
                "hwi_device_id": self.device_id_watch,
                "timezone_offset": -4,
                "estimated_timestamp": False,
                "dummy_data": True
                }

            self.syntrillo_database_manager.insert_tenovi_raw_measurement(
                device_name="Tenovi Watch",
                metric_name="steps",
                value_1=value1_str,
                value_2="0.00",
                timestamp_zulu=timestamp_zulu,
                timezone_offset=-4,
                data_json=json.dumps(data_steps, default=str)
            )

        return None

    def generate_pillbox_device_data(self, date_start: datetime, date_end: datetime):
        """
        Generate pillbox data for the given date range.
        """
        date = date_start
        i = 0

        while date < date_end:
            i += 1
            date += timedelta(days=1)

        return None

    def generate_all_devices_data_wrapup(self, date_start: datetime, date_end: datetime):
        """
        Generate data for all devices for the given date range.
        """
        _ = self.generate_BMP_device_data(date_start, date_end)
        _ = self.generate_watch_device_data(date_start, date_end)
        _ = self.generate_pillbox_device_data(date_start, date_end)


    def delete_dummy_records(self) -> dict:
        """
        Delete all dummy records

        Returns:
            log (dict): The log of the request, with "success" key set to True or False
        """
        try:
            with self.syntrillo_database_manager.conn.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM tenovi_raw_measurements
                    WHERE syntrillo_internal_key = %s
                    AND JSON_UNQUOTE(JSON_EXTRACT(data_json, '$.dummy_data')) = true
                    """,
                    (self.syntrillo_internal_key.bytes,)
                )
                self.syntrillo_database_manager.conn.commit()
                log = {
                    "success": True
                }
        except pymysql.MySQLError as e:
            log = {
                "success": False,
                "error": str(e)
            }

        return log


if __name__ == "__main__":

    lookup_codes_management = LookUpCodesManagement()
    entry = lookup_codes_management.retrieve_entry_by_healthie_user_id("1035117")

    data_generator = TenoviDummyDataGenerator(entry["syntrillo_internal_key"], verbose=True)

    data_generator.delete_dummy_records()

    data_generator.set_patient_state(
        patient_state_blood_pressure="healthy",
        patient_state_heart_rate="healthy",
        patient_state_steps="healthy",
    )

    _ = data_generator.generate_BMP_device_data(datetime(2021, 1, 1), datetime(2021, 1, 5))

    _ = data_generator.generate_watch_device_data(datetime(2021, 1, 1), datetime(2021, 1, 5))

