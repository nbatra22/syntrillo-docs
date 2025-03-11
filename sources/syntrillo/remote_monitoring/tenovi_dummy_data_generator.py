# Path: ./sources/syntrillo/remote_monitoring/tenovi_dummy_data_generator.py
# Path: ./sources/syntrillo/remote_monitoring/dummy_data_generator.py

import uuid
from datetime import datetime, timedelta, timezone
import random
import json
import pymysql

from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.api_tenovi.devices import Devices
from syntrillo.api_tenovi.device_types import DeviceTypes
from syntrillo.api_tenovi.device_measurements import DeviceMeasurements
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager

from aws_lambda_powertools import Logger
logger = Logger(service="DUMMY_DATA_GENERATOR")

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

        logger.info(f"[DUMMY_DATA_GENERATOR] <DEVICES_RETREIVE_FROM_TENOVI> devices {devices}, pseudo_code_for_tenovi_phi_access {self.pseudo_code_for_tenovi_phi_access}")

        # OLEMAITRE: the 3 lines below will avoid errors like : 'TenoviDummyDataGenerator' object has no attribute 'device_id_watch'
        self.device_id_BMP=None
        self.device_id_pillbox=None
        self.device_id_watch=None

        for device in devices:
            if device['device']['name'] in [DeviceTypes.TENOVI_DEVICE_NAME__BPM_LARGE, DeviceTypes.TENOVI_DEVICE_NAME__BPM_SMALL] :
                self.device_id_BMP = device["id"]
            elif device['device']['name'] == DeviceTypes.TENOVI_DEVICE_NAME__PILLBOX:
                self.device_id_pillbox = device["id"]
            elif device['device']['name'] == DeviceTypes.TENOVI_DEVICE_NAME__WATCH:
                self.device_id_watch = device["id"]

        if verbose:
            print(f"TenoviDummyDataGenerator: {self.healthie_user_id} - {self.syntrillo_internal_key} - {self.pseudo_code_for_tenovi_phi_access}")
            print(f"TenoviDummyDataGenerator: {self.device_id_BMP} - {self.device_id_pillbox} - {self.device_id_watch}")

    def set_patient_state(
        self,
        patient_state_blood_pressure: str,
        patient_state_heart_rate: str,
        patient_state_steps: str,
        patient_state_medication_adherence: str,
        patient_state_medication_expected_pattern: str,
        patient_state_irregular_heartbeat: bool = False,
        ) -> None:
        """
        Set the patient state to generate the data accordingly

        Args:
            patient_state_blood_pressure (str): "healthy", "hypertensive", "hypotensive"
            patient_state_heart_rate (str): "healthy", "tachycardic", "bradycardic"
            patient_state_steps (str): "healthy", "sedentary", "active"
            patient_state_medication_adherence (str): "perfect", "partial", "poor"
            patient_state_medication_expected_pattern (str): "twice daily", "daily AM", "daily PM"

        """


        # ---------------------- Blood Pressure ----------------------

        self.patient_state_irregular_heartbeat = patient_state_irregular_heartbeat

        if patient_state_irregular_heartbeat:
            self.irregular_heartbeat_probability = 0.1
        else:
            self.irregular_heartbeat_probability = 0.0

        self.patient_state_blood_pressure = patient_state_blood_pressure

        if patient_state_blood_pressure == "healthy" or patient_state_blood_pressure == "no_data":
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

        # ---------------------- Heart Rate ----------------------

        self.patient_state_heart_rate = patient_state_heart_rate

        if patient_state_heart_rate == "healthy" or patient_state_heart_rate == "no_data":
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

        # ---------------------- Steps ----------------------

        self.patient_state_steps = patient_state_steps

        # looks like these are hourly steps
        if patient_state_steps == "healthy" or patient_state_steps == "no_data":
            self.steps_min = 500
            self.steps_max = 1000
            self.steps_mean = 750
            self.steps_var = 5
        elif patient_state_steps == "sedentary":
            self.steps_min = 100
            self.steps_max = 500
            self.steps_mean = 300
            self.steps_var = 5
        elif patient_state_steps == "active":
            self.steps_min = 1000
            self.steps_max = 1500
            self.steps_mean = 1250
            self.steps_var = 5

        # ---------------------- Pillbox ----------------------

        self.patient_state_medication_expected_pattern = patient_state_medication_expected_pattern
        self.patient_state_medication_adherence = patient_state_medication_adherence

        if patient_state_medication_adherence == "perfect" or patient_state_medication_adherence == "no_data":
            self.medication_adherence_missed_rate_weekdays = 0.00
            self.medication_adherence_missed_rate_weekends = 0.00
            self.medication_adherence_overdose_rate = 0.0
            self.pillbox_refill_rate = 0.20
        elif patient_state_medication_adherence == "partial":
            self.medication_adherence_missed_rate_weekdays = 0.20
            self.medication_adherence_missed_rate_weekends = 0.25
            self.medication_adherence_overdose_rate = 0.01
            self.pillbox_refill_rate = 0.10
        elif patient_state_medication_adherence == "poor":
            self.medication_adherence_missed_rate_weekdays = 0.50
            self.medication_adherence_missed_rate_weekends = 0.60
            self.medication_adherence_overdose_rate = 0.05
            self.pillbox_refill_rate = 0.05


    def generate_BPM_data_point(self):
        """
        Generate a single blood pressure measurement data point
        """
        systolic = random.gauss(self.systolic_mean, self.systolic_var)
        diastolic = random.gauss(self.diastolic_mean, self.diastolic_var)
        pulse = random.gauss(self.pulse_mean, self.pulse_var)

        systolic = round(max(self.systolic_min, min(systolic, self.systolic_max)), 0)
        diastolic = round(max(self.diastolic_min, min(diastolic, self.diastolic_max)), 0)
        pulse = round(max(self.pulse_min, min(pulse, self.pulse_max)), 0)

        if self.patient_state_irregular_heartbeat:
            irregular_heartbeat = random.random() < self.irregular_heartbeat_probability
        else:
            irregular_heartbeat = False

        return systolic, diastolic, pulse, irregular_heartbeat

    def generate_BPM_device_data(self, date_start: datetime, date_end: datetime):
        """
        Generate blood pressure data for the given date range.
        """
        date = date_start
        i = 0

        while date < date_end:
            i += 1
            if random.random() > 0.1:
                date += timedelta(days=1)

            timestamp = date + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
            timestamp_zulu = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            created1 = timestamp + timedelta(minutes=random.randint(0, 59))
            created2 = created1 + timedelta(microseconds=random.randint(100, 999))
            created3 = created2 + timedelta(microseconds=random.randint(100, 999))

            created1_str = created1.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            created2_str = created2.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            created3_str = created3.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


            # ----------------------
            # blood pressure data
            if self.patient_state_blood_pressure != "no_data":

                systolic, diastolic, pulse, irregular_heartbeat = self.generate_BPM_data_point()

                value1_str = f"{systolic:.2f}"
                value2_str = f"{diastolic:.2f}"

                data_bp = {
                    "metric": DeviceMeasurements.TENOVI_METRICS_BPM_BLOOD_PRESSURE,
                    "created": created1_str,
                    "value_1": value1_str,
                    "value_2": value2_str,
                    "timestamp": timestamp_zulu,
                    "patient_id": self.healthie_user_id,
                    "device_name": DeviceTypes.TENOVI_DEVICE_NAME__BPM_LARGE,
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
                    device_name=DeviceTypes.TENOVI_DEVICE_NAME__BPM_LARGE,
                    metric_name=DeviceMeasurements.TENOVI_METRICS_BPM_BLOOD_PRESSURE,
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
                    "metric": DeviceMeasurements.TENOVI_METRICS_BPM_PULSE,
                    "created": created2_str,
                    "value_1": value1_str,
                    "value_2": "0.00",
                    "timestamp": timestamp_zulu,
                    "patient_id": self.healthie_user_id,
                    "device_name": DeviceTypes.TENOVI_DEVICE_NAME__BPM_LARGE,
                    "sensor_code": "10",
                    "filter_params": {"measurement_index": 200+i},
                    "hardware_uuid": "FB5E23D5E7F7",
                    "hwi_device_id": self.device_id_BMP,
                    "timezone_offset": -4,
                    "estimated_timestamp": False,
                    "dummy_data": True
                    }

                self.syntrillo_database_manager.insert_tenovi_raw_measurement(
                    device_name=DeviceTypes.TENOVI_DEVICE_NAME__BPM_LARGE,
                    metric_name=DeviceMeasurements.TENOVI_METRICS_BPM_PULSE,
                    value_1=value1_str,
                    value_2="0.00",
                    timestamp_zulu=timestamp_zulu,
                    timezone_offset=-4,
                    data_json=json.dumps(data_hr, default=str)
                )

                # ----------------------
                # irregular heartbeat
                if irregular_heartbeat:
                    data_ihb = {
                        "metric": DeviceMeasurements.TENOVI_METRICS_BPM_IRREGULAR_HEARTBEAT,
                        "created": created3_str,
                        "value_1": "1.00",
                        "value_2": "0.00",
                        "timestamp": timestamp_zulu,
                        "patient_id": self.healthie_user_id,
                        "device_name": DeviceTypes.TENOVI_DEVICE_NAME__BPM_LARGE,
                        "sensor_code": "10",
                        "filter_params": {"measurement_index": 200+i},
                        "hardware_uuid": "FB5E23D5E7F7",
                        "hwi_device_id": self.device_id_BMP,
                        "timezone_offset": -4,
                        "estimated_timestamp": False,
                        "dummy_data": True
                        }

                    self.syntrillo_database_manager.insert_tenovi_raw_measurement(
                        device_name=DeviceTypes.TENOVI_DEVICE_NAME__BPM_LARGE,
                        metric_name=DeviceMeasurements.TENOVI_METRICS_BPM_IRREGULAR_HEARTBEAT,
                        value_1="1.00",
                        value_2="0.00",
                        timestamp_zulu=timestamp_zulu,
                        timezone_offset=-4,
                        data_json=json.dumps(data_ihb, default=str)
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

            timestamp = date # + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
            created = timestamp + timedelta(minutes=random.randint(0, 59))

            created_str = created.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            timestamp_zulu = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            heart_rate_average, heart_rate_max, steps = self.generate_watch_data_point(timestamp)

            # ----------------------
            # HR stats
            if self.patient_state_heart_rate != "no_data":
                value1_str = f"{heart_rate_average:.2f}"
                value2_str = f"{heart_rate_max:.2f}"

                data_hr_stats = {
                    "metric": DeviceMeasurements.TENOVI_METRICS_WATCH_HEART_RATE_STATISTICS,
                    "created": created_str,
                    "value_1": value1_str,
                    "value_2": value2_str,
                    "timestamp": timestamp_zulu,
                    "patient_id": self.healthie_user_id,
                    "device_name": DeviceTypes.TENOVI_DEVICE_NAME__WATCH,
                    "sensor_code": "15",
                    "filter_params": {"period": 60, "wearable_code": 0, "max_heart_rate": 91, "min_heart_rate": 0, "average_heart_rate": 80},
                    "hardware_uuid": "FB5E23D5E7F7",
                    "hwi_device_id": self.device_id_watch,
                    "timezone_offset": -4,
                    "estimated_timestamp": False,
                    "dummy_data": True
                    }

                self.syntrillo_database_manager.insert_tenovi_raw_measurement(
                    device_name=DeviceTypes.TENOVI_DEVICE_NAME__WATCH,
                    metric_name=DeviceMeasurements.TENOVI_METRICS_WATCH_HEART_RATE_STATISTICS,
                    value_1=value1_str,
                    value_2=value2_str,
                    timestamp_zulu=timestamp_zulu,
                    timezone_offset=-4,
                    data_json=json.dumps(data_hr_stats, default=str)
                )

            # ----------------------
            # steps
            if self.patient_state_steps != "no_data":
                value1_str = f"{steps:.2f}"

                data_steps = {
                    "metric": DeviceMeasurements.TENOVI_METRICS_WATCH_STEPS,
                    "created": created_str,
                    "value_1": value1_str,
                    "value_2": "0.00",
                    "timestamp": timestamp_zulu,
                    "patient_id": self.healthie_user_id,
                    "device_name": DeviceTypes.TENOVI_DEVICE_NAME__WATCH,
                    "sensor_code": "15",
                    "filter_params": {"wearable_code": 0},
                    "hardware_uuid": "FB5E23D5E7F7",
                    "hwi_device_id": self.device_id_watch,
                    "timezone_offset": -4,
                    "estimated_timestamp": False,
                    "dummy_data": True
                    }

                self.syntrillo_database_manager.insert_tenovi_raw_measurement(
                    device_name=DeviceTypes.TENOVI_DEVICE_NAME__WATCH,
                    metric_name=DeviceMeasurements.TENOVI_METRICS_WATCH_STEPS,
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

        Args:
            date_start (datetime): The start date
            date_end (datetime): The end date
        """

        # time of date_start should be 00:00:00
        date_start = datetime(date_start.year, date_start.month, date_start.day, 0, 0, 0, tzinfo=timezone(timedelta(hours=-4)))

        # time of date_end should be 23:59:59
        date_end = datetime(date_end.year, date_end.month, date_end.day, 23, 59, 59, tzinfo=timezone(timedelta(hours=-4)))

        date = date_start
        i = 0

        while date < date_end:

            # ----------------------
            # refill events on weekends
            if self.pillbox_refill_rate > random.random() and date.weekday() in [5, 6]:
                # Make sure timestamp is on the day of 'date' and in the morning 7 to 11 am EST time (UTC-4)
                hour = random.randint(7, 22)
                minute = random.randint(0, 59)
                timestamp = datetime(date.year, date.month, date.day, hour, minute, tzinfo=timezone(timedelta(hours=-4)))
                timestamp_zulu = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

                created = timestamp + timedelta(minutes=random.randint(0, 59))
                created_str = created.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

                data_pillbox_refill_initiated = {
                        "metric": DeviceMeasurements.TENOVI_METRICS_PILLBOX_REFILL_INITIATED,
                        "created": created_str,
                        "value_1": "1.00",
                        "value_2": "0.00",
                        "timestamp": timestamp_zulu,
                        "patient_id": self.healthie_user_id,
                        "device_name": DeviceTypes.TENOVI_DEVICE_NAME__PILLBOX,
                        "sensor_code": "21",
                        "filter_params": None,
                        "hardware_uuid": "FB5E23D5E7F7",
                        "hwi_device_id": self.device_id_watch,
                        "timezone_offset": -4,
                        "estimated_timestamp": False,
                        "dummy_data": True
                        }

                self.syntrillo_database_manager.insert_tenovi_raw_measurement(
                    device_name=DeviceTypes.TENOVI_DEVICE_NAME__PILLBOX,
                    metric_name=DeviceMeasurements.TENOVI_METRICS_PILLBOX_REFILL_INITIATED,
                    value_1="1.00",
                    value_2="0.00",
                    timestamp_zulu=timestamp_zulu,
                    timezone_offset=-4,
                    data_json=json.dumps(data_pillbox_refill_initiated, default=str)
                )

                for value_1 in range(1,8) :  # sun to sat
                    for value_2 in range(1,3): # amp and pm
                        # add random seconds to the timestamp and created
                        timestamp = timestamp + timedelta(seconds=random.randint(0, 59))
                        created = timestamp + timedelta(seconds=random.randint(0, 59))

                        created_str = created.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                        timestamp_zulu = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

                        # format value_1 and value_2 to strings with 2 decimals : eg "1.00"
                        value_1_str = f"{value_1:0.2f}"
                        value_2_str = f"{value_2:0.2f}"

                        # compartment is the day of the week and AM/PM from timestamp, example 'Wednesday AM'
                        compartment = timestamp.strftime("%A") + " " + ("AM" if timestamp.hour < 12 else "PM")

                        data_pillbox_refilled = {
                            "metric": DeviceMeasurements.TENOVI_METRICS_PILLBOX_REFILLED,
                            "created": created_str,
                            "value_1": value_1_str,
                            "value_2": value_2_str,
                            "timestamp": timestamp_zulu,
                            "patient_id": self.healthie_user_id,
                            "device_name": "Tenovi Pillbox",
                            "sensor_code": "21",
                            "filter_params": { "compartment": compartment },
                            "hardware_uuid": "FB5E23D5E7F7",
                            "hwi_device_id": self.device_id_pillbox,
                            "timezone_offset": -4,
                            "estimated_timestamp": False,
                            "dummy_data": True
                        }

                        self.syntrillo_database_manager.insert_tenovi_raw_measurement(
                            device_name=DeviceTypes.TENOVI_DEVICE_NAME__PILLBOX,
                            metric_name=DeviceMeasurements.TENOVI_METRICS_PILLBOX_REFILLED,
                            value_1=value_1_str,
                            value_2=value_2_str,
                            timestamp_zulu=timestamp_zulu,
                            timezone_offset=-4,
                            data_json=json.dumps(data_pillbox_refilled, default=str)
                        )

            # -----------------------
            # AM events

            if ( self.patient_state_medication_expected_pattern in ["twice_daily", "daily_am"] \
                and ( \
                        ( date.weekday() < 5 and self.medication_adherence_missed_rate_weekdays < random.random() ) \
                    or  ( date.weekday() >= 5 and self.medication_adherence_missed_rate_weekends < random.random() ) \
                ) ) \
                or self.medication_adherence_overdose_rate > random.random():

                # Make sure timestamp is on the day of 'date' and in the morning 7 to 11 am EST time (UTC-4)
                hour = random.randint(7, 10)  # 10 to ensure range is up to 11 am
                minute = random.randint(0, 59)
                timestamp = datetime(date.year, date.month, date.day, hour, minute, tzinfo=timezone(timedelta(hours=-4)))

                created = timestamp + timedelta(minutes=random.randint(0, 59))

                created_str = created.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                timestamp_zulu = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

                # value1_str is the day of the week 1=Sun ... 7=Sat
                weekday = timestamp.weekday() + 2 if timestamp.weekday() < 6 else 1
                value1_str = f"{weekday:0.2f}"

                # compartment is the day of the week and AM/PM from timestamp, example 'Wednesday AM'
                compartment = timestamp.strftime("%A") + " " + ("AM" if timestamp.hour < 12 else "PM")

                # pillbox opened event
                data_pillbox_opened = {
                    "metric": DeviceMeasurements.TENOVI_METRICS_PILLBOX_OPENED,
                    "created": created_str,
                    "value_1": value1_str,
                    "value_2": "1.00",  # 1=AM, 2=PM
                    "timestamp": timestamp_zulu,
                    "patient_id": self.healthie_user_id,
                    "device_name": DeviceTypes.TENOVI_DEVICE_NAME__PILLBOX,
                    "sensor_code": "21",
                    "filter_params": { "compartment": compartment },
                    "hardware_uuid": "FB5E23D5E7F7",
                    "hwi_device_id": self.device_id_pillbox,
                    "timezone_offset": -4,
                    "estimated_timestamp": False,
                    "dummy_data": True
                    }

                self.syntrillo_database_manager.insert_tenovi_raw_measurement(
                    device_name=DeviceTypes.TENOVI_DEVICE_NAME__PILLBOX,
                    metric_name=DeviceMeasurements.TENOVI_METRICS_PILLBOX_OPENED,
                    value_1=value1_str,
                    value_2="1.00",
                    timestamp_zulu=timestamp_zulu,
                    timezone_offset=-4,
                    data_json=json.dumps(data_pillbox_opened, default=str)
                )

            # -----------------------
            # PM events

            if ( self.patient_state_medication_expected_pattern in ["twice_daily", "daily_pm"] \
                and ( \
                        ( date.weekday() < 5 and self.medication_adherence_missed_rate_weekdays < random.random() ) \
                    or  ( date.weekday() >= 5 and self.medication_adherence_missed_rate_weekends < random.random() ) \
                ) ) \
                or self.medication_adherence_overdose_rate > random.random():

                # Make sure timestamp is on the day of 'date' and in the morning 7 to 11 am EST time (UTC-4)
                hour = random.randint(18, 22)
                minute = random.randint(0, 59)
                timestamp = datetime(date.year, date.month, date.day, hour, minute, tzinfo=timezone(timedelta(hours=-4)))

                created = timestamp + timedelta(minutes=random.randint(0, 59))

                created_str = created.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                timestamp_zulu = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

                # value1_str is the day of the week 1=Sun ... 7=Sat
                weekday = timestamp.weekday() + 2 if timestamp.weekday() < 6 else 1
                value1_str = f"{weekday:0.2f}"

                # compartment is the day of the week and AM/PM from timestamp, example 'Wednesday AM'
                compartment = timestamp.strftime("%A") + " " + ("AM" if timestamp.hour < 12 else "PM")

                # pillbox opened event
                data_pillbox_opened = {
                    "metric": DeviceMeasurements.TENOVI_METRICS_PILLBOX_OPENED,
                    "created": created_str,
                    "value_1": value1_str,
                    "value_2": "2.00",  # 1=AM, 2=PM
                    "timestamp": timestamp_zulu,
                    "patient_id": self.healthie_user_id,
                    "device_name": DeviceTypes.TENOVI_DEVICE_NAME__PILLBOX,
                    "sensor_code": "21",
                    "filter_params": { "compartment": compartment },
                    "hardware_uuid": "FB5E23D5E7F7",
                    "hwi_device_id": self.device_id_pillbox,
                    "timezone_offset": -4,
                    "estimated_timestamp": False,
                    "dummy_data": True
                    }

                self.syntrillo_database_manager.insert_tenovi_raw_measurement(
                    device_name=DeviceTypes.TENOVI_DEVICE_NAME__PILLBOX,
                    metric_name=DeviceMeasurements.TENOVI_METRICS_PILLBOX_OPENED,
                    value_1=value1_str,
                    value_2="2.00",
                    timestamp_zulu=timestamp_zulu,
                    timezone_offset=-4,
                    data_json=json.dumps(data_pillbox_opened, default=str)
                )


            # next day unless overdose
            if self.medication_adherence_overdose_rate < random.random():
                i += 1
                date += timedelta(days=1)


        return None

    def generate_all_devices_data_wrapup(self, date_start: datetime, date_end: datetime):
        """
        Generate data for all devices for the given date range.
        """

        _ = self.generate_BPM_device_data(date_start, date_end)

        _ = self.generate_watch_device_data(date_start, date_end)

        if self.patient_state_medication_adherence != "no_data":
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
        patient_state_blood_pressure="no_data",
        patient_state_heart_rate="no_data",
        patient_state_steps="no_data",
        patient_state_medication_adherence="perfect",
        patient_state_medication_expected_pattern="twice daily",
        patient_state_irregular_heartbeat=False,
    )

    # _ = data_generator.generate_BPM_device_data(datetime(2021, 1, 1), datetime(2021, 1, 5))

    # _ = data_generator.generate_watch_device_data(datetime(2021, 1, 1), datetime(2021, 1, 5))

    _ = data_generator.generate_pillbox_device_data(datetime(2024, 4, 1), datetime(2024, 5, 1))
