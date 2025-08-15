# Path: ./sources/syntrillo/remote_monitoring/syntrillo_database_manager.py

import uuid
import json
import pymysql
from typing import Optional, Tuple, List, Union
from datetime import datetime, timedelta, timezone
import pandas as pd

from syntrillo.databases_management.connection import DatabaseConnection
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.api_tenovi.device_types import DeviceTypes
from syntrillo.stroke_risk_score_v2.models.treatment_compliance import TreatmentCompliance
from syntrillo.system.logger import logger
from syntrillo.stroke_risk_score_v2.models.srs_form import SRSFormResponse
from syntrillo.remote_monitoring.constants import BLOOD_PRESSURE_METRIC_NAME, PULSE_METRIC_NAME


class SyntrilloDatabaseManager:
    """
    A class to manage remote monitoring data in the Syntrillo PHI database.

    Attributes:
       TENOVI_DEVICE_NAMES : list, with valid Tenovi device names

    """

    # Tenovi devices
    TENOVI_DEVICE_NAMES=[
        DeviceTypes.TENOVI_DEVICE_NAME__WATCH,
        DeviceTypes.TENOVI_DEVICE_NAME__PILLBOX,
        DeviceTypes.TENOVI_DEVICE_NAME__BPM_LARGE,
        DeviceTypes.TENOVI_DEVICE_NAME__BPM_SMALL,
        DeviceTypes.TENOVI_DEVICE_NAME__BPM_PREFIX, # will retrieve all BMP devices
    ]


    def __init__(self, syntrillo_internal_key: uuid.UUID):
        """
            For a given patient, manage data located in our Syntrillo PHI database

            Args:
                syntrillo_internal_key (uuid.UUID): The internal key for the patient
        """

        self.syntrillo_internal_key = syntrillo_internal_key

        # connect to our database
        db_conn = DatabaseConnection(DatabaseConnection.HEALTH_INFO_DB)
        self.conn, _ = db_conn.create_connection()

    def get_latest_record_for_tenovi_device(self, device_name: str) -> Tuple[dict, dict]:
        """
            Get the latest record for a given device.

            Used to get the latest created time for a device to sync data from Tenovi to Healthie.

            Using created time (in Tenovi server) instead of timestemp is more accurate => no duplicate, no gap if device late to sync.

            Args:
                device_name (str): The name of the device

            Returns a tuple:
                record (dict): The latest record for the device, including the created time
                log (dict): The log of the request

        """

       # Check if device_name is valid
        if device_name not in self.TENOVI_DEVICE_NAMES:
            log = {
                "success": False,
                "error": f"Invalid device_name: {device_name}"
            }
            return None, log

        try:
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT *, JSON_UNQUOTE(JSON_EXTRACT(data_json, '$.created')) as 'created'
                    FROM tenovi_raw_measurements
                    WHERE syntrillo_internal_key = %s AND device_name = %s
                    ORDER BY JSON_UNQUOTE(JSON_EXTRACT(data_json, '$.created')) DESC
                    LIMIT 1
                    """,
                    (self.syntrillo_internal_key.bytes, device_name)
                )
                record = cursor.fetchone()
                log = {
                    "success": True,
                }
        except pymysql.MySQLError as e:
            log = {
                "success": False,
                "error": str(e)
            }
            record = None

        return record, log

    def insert_tenovi_raw_measurement(
        self,
        device_name: str,
        metric_name: str,
        value_1: str,
        value_2: str,
        timestamp_zulu: str,
        timezone_offset: str,
        data_json: str
        ) -> dict :
        """
            Insert a new raw measurement for a Tenovi device

            Args:
                device_name (str): The name of the device
                metric_name (str): The name of the metric
                value_1 (str): The first value
                value_2 (str): The second value
                timestamp_zulu (str): The timestamp (zulu time) from the device
                timezone_offset (str): The timezone offset from the device
                data_json (str): The data in JSON format

            Returns:
                log (dict): The log of the request, with "success" key set to True or False

        """

        # Check if device_name is valid
        if device_name not in self.TENOVI_DEVICE_NAMES:
            log = {
                "success": False,
                "error": f"Invalid device_name: {device_name}"
            }
            return log

        try:

            # Apply the timezone offset to get the local time, in the isoformat format
            offset = timedelta(hours=timezone_offset)
            tz = timezone(offset)
            zulu_time = datetime.strptime(timestamp_zulu, "%Y-%m-%dT%H:%M:%S.%fZ")
            local_time = zulu_time.replace(tzinfo=timezone.utc).astimezone(tz)
            timestamp_local = local_time.isoformat(timespec='microseconds')

            with self.conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO tenovi_raw_measurements
                    (syntrillo_internal_key, device_name, metric_name, value_1, value_2, timestamp_local, data_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (self.syntrillo_internal_key.bytes, device_name, metric_name, value_1, value_2, timestamp_local, data_json)
                )
                self.conn.commit()
                log = {
                    "success": True
                }
        except pymysql.MySQLError as e:
            log = {
                "success": False,
                "error": str(e)
            }

        return log

    def get_summary_devices_report(self) -> Tuple[dict, dict]:
        """
            Get a summary report of the devices for the patient. For each device, the report should include:
            - number of data points
            - latest timestamp
            - latest battery level ( it is the 'battery_percentage' metric )

            Returns a tuple:
                report (dict): The summary report
                log (dict): The log of the request

        """

        log = { "success": True }

        try:
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT
                        device_name,
                        COUNT(*) as 'number_of_data_points_in_syntrillo_database',
                        MAX(timestamp_local) as 'latest__timestamp_local__in_syntrillo_database' ,
                        MAX(JSON_UNQUOTE(JSON_EXTRACT(data_json, '$.created'))) as 'latest__tenovi_server_created__in_syntrillo_database'
                    FROM tenovi_raw_measurements
                    WHERE syntrillo_internal_key = %s
                    GROUP BY device_name
                    """,
                    (self.syntrillo_internal_key.bytes,)
                )
                report = cursor.fetchall()

        except pymysql.MySQLError as e:
            log = {
                "success": False,
                "error": str(e)
            }
            report = None

        return report, log

    def get_metric_records_after_local_timestamp(self, timestamp_local: str, metric_name: str) -> Tuple[dict, dict]:
        """
            Get all records for a device metric after a given local timestamp.

            Args:
                timestamp_local (str): The timestamp (local patient time) to filter by
                metric_name (str): The name of the metric

            Returns a tuple:
                records (dict): The records for the metric
                log (dict): The log of the request

        """

        try:
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                if timestamp_local is None:
                    cursor.execute(
                        f"""
                        SELECT * FROM tenovi_raw_measurements
                        WHERE metric_name = '{metric_name}'
                        AND syntrillo_internal_key = %s
                        ORDER BY timestamp_local ASC
                        """,
                        (self.syntrillo_internal_key.bytes,)
                    )
                else:
                    cursor.execute(
                        f"""
                        SELECT * FROM tenovi_raw_measurements
                        WHERE metric_name = '{metric_name}'
                        AND syntrillo_internal_key = %s
                        AND timestamp_local > %s
                        ORDER BY timestamp_local ASC
                        """,
                        (self.syntrillo_internal_key.bytes, timestamp_local)
                    )
                records = cursor.fetchall()
                log = {
                    "success": True,
                }
        except pymysql.MySQLError as e:
            log = {
                "success": False,
                "error": str(e)
            }
            records = None

        return records, log

    def get_daily_stats_metric_records_after_local_timestamp(self, timestamp_local: str, metric_name: str) -> Tuple[dict, dict]:
        """
            Get daily stats records for a device metric after a given local timestamp, and one day before the latest data point available.

            TODO : use pandas and numpy to calculate the daily stats

            Args:
                timestamp_local (str): The timestamp (local patient time) to filter by
                metric_name (str): The name of the metric

            Returns a tuple:
                records (dict): The records for the metric
                log (dict): The log of the request

        """

        try:
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                if timestamp_local is None:
                    query = f"""
                        SELECT
                            DATE(timestamp_local) as day,
                            MIN(CAST(value_1 AS DECIMAL(10, 2))) as min_value_1,
                            MIN(CAST(value_2 AS DECIMAL(10, 2))) as min_value_2,
                            MAX(CAST(value_1 AS DECIMAL(10, 2))) as max_value_1,
                            MAX(CAST(value_2 AS DECIMAL(10, 2))) as max_value_2,
                            SUM(CAST(value_1 AS DECIMAL(10, 2))) as sum_value_1,
                            SUM(CAST(value_2 AS DECIMAL(10, 2))) as sum_value_2,
                            AVG(CAST(value_1 AS DECIMAL(10, 2))) as avg_value_1,
                            AVG(CAST(value_2 AS DECIMAL(10, 2))) as avg_value_2
                        FROM
                            tenovi_raw_measurements
                        WHERE
                            metric_name = '{metric_name}'
                            AND syntrillo_internal_key = %s
                        GROUP BY
                            DATE(timestamp_local)
                        HAVING
                            day < (
                                SELECT DATE_SUB(MAX(DATE(timestamp_local)), INTERVAL 1 DAY)
                                FROM tenovi_raw_measurements
                                WHERE
                                    metric_name = '{metric_name}'
                                    AND syntrillo_internal_key = %s
                            )
                        ORDER BY
                            day ASC
                    """
                    cursor.execute(query, (self.syntrillo_internal_key.bytes, self.syntrillo_internal_key.bytes,))
                else:
                    query = f"""
                        SELECT
                            DATE(timestamp_local) as day,
                            MIN(CAST(value_1 AS DECIMAL(10, 2))) as min_value_1,
                            MIN(CAST(value_2 AS DECIMAL(10, 2))) as min_value_2,
                            MAX(CAST(value_1 AS DECIMAL(10, 2))) as max_value_1,
                            MAX(CAST(value_2 AS DECIMAL(10, 2))) as max_value_2,
                            SUM(CAST(value_1 AS DECIMAL(10, 2))) as sum_value_1,
                            SUM(CAST(value_2 AS DECIMAL(10, 2))) as sum_value_2,
                            AVG(CAST(value_1 AS DECIMAL(10, 2))) as avg_value_1,
                            AVG(CAST(value_2 AS DECIMAL(10, 2))) as avg_value_2

                        FROM
                            tenovi_raw_measurements
                        WHERE
                            metric_name = '{metric_name}'
                            AND syntrillo_internal_key = %s
                            AND DATE(timestamp_local) > DATE(%s)
                        GROUP BY
                            DATE(timestamp_local)
                        HAVING
                            day < (
                                SELECT DATE_SUB(MAX(DATE(timestamp_local)), INTERVAL 1 DAY)
                                FROM tenovi_raw_measurements
                                WHERE
                                    metric_name = '{metric_name}'
                                    AND syntrillo_internal_key = %s
                            )
                        ORDER BY
                            day ASC
                    """
                    cursor.execute(query, (self.syntrillo_internal_key.bytes, timestamp_local, self.syntrillo_internal_key.bytes))

                records = cursor.fetchall()

                log = {
                    "success": True,
                }
        except pymysql.MySQLError as e:
            log = {
                "success": False,
                "error": str(e)
            }
            records = None

        return records, log

    def get_first_tenovi_device_data(self, device_name: str) -> Tuple[dict, dict]:
        """
            Get the first record for a given device, based on ite timestamp_local.

            For example used in pillbox data analysis to produce correct stats, based on usage duration.

            Args:
                device_name (str): The name of the device

            Returns a tuple:
                record (dict): The latest record for the device.
                log (dict): The log of the request

        """

       # Check if device_name is valid
        if device_name not in self.TENOVI_DEVICE_NAMES:
            log = {
                "success": False,
                "error": f"Invalid device_name: {device_name}"
            }
            return None, log

        try:
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                if device_name == DeviceTypes.TENOVI_DEVICE_NAME__BPM_PREFIX:
                    cursor.execute(
                        """
                        SELECT *
                        FROM tenovi_raw_measurements
                        WHERE syntrillo_internal_key = %s AND ( device_name = %s OR device_name = %s )
                        ORDER BY timestamp_local ASC
                        LIMIT 1
                        """,
                        (
                            self.syntrillo_internal_key.bytes,
                            DeviceTypes.TENOVI_DEVICE_NAME__BPM_LARGE,
                            DeviceTypes.TENOVI_DEVICE_NAME__BPM_SMALL
                        )
                    )
                else:
                    cursor.execute(
                        """
                        SELECT *
                        FROM tenovi_raw_measurements
                        WHERE syntrillo_internal_key = %s AND device_name = %s
                        ORDER BY timestamp_local ASC
                        LIMIT 1
                        """,
                        (
                            self.syntrillo_internal_key.bytes,
                            device_name
                         )
                    )

                record = cursor.fetchone()
                log = {
                    "success": True,
                }
        except pymysql.MySQLError as e:
            log = {
                "success": False,
                "error": str(e)
            }
            record = None

        return record, log


    def get_tenovi_device_data(
        self,
        device_name: str,
        start_date: datetime,
        end_date: datetime,
        include_battery: bool = False
        ) -> Tuple[pd.DataFrame, dict]:
        """
            Get all records for a device between two dates

            Args:
                device_name (str): The name of the device
                start_date (datetime): The start date. None allowed.
                end_date (datetime): The end date. If None, the current date will be used.
                include_battery (bool): Include the battery percentage metric (default is False)

            Returns a tuple:
                df (pd.DataFrame): The records for the device, as a Pandas DataFrame
                log (dict): The log of the request

        """

       # Check if device_name is valid
        if device_name not in self.TENOVI_DEVICE_NAMES:
            log = {
                "success": False,
                "error": f"Invalid device_name: {device_name}"
            }
            return None, log

        # deal with None start_date, end_date
        if start_date is None:
            start_date = datetime(2000)

        if end_date is None:
            end_date = datetime.now()

        # run query
        try:
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                query = f"""
                SELECT device_name, metric_name, value_1, value_2, timestamp_local
                FROM tenovi_raw_measurements
                WHERE syntrillo_internal_key = %s
                AND device_name = %s
                AND (metric_name <> 'battery_percentage' OR %s)
                AND ( timestamp_local BETWEEN %s AND %s )
                ORDER BY timestamp_local ASC
                """
                cursor.execute(
                    query,
                    (
                        self.syntrillo_internal_key.bytes,
                        device_name,
                        include_battery,
                        start_date.isoformat(), end_date.isoformat() # using isoformat everywhere, to select base on local time, and not rely on mySQL time features
                     )
                )
                records = cursor.fetchall()  # Fetch all records
                log = {
                    "success": True,
                }
        except pymysql.MySQLError as e:
            log = {
                "success": False,
                "error": str(e)
            }
            records = None

        # Check if records are found
        if records:
            df = pd.DataFrame(records)
        else:
            df = pd.DataFrame()  # Return an empty DataFrame if no records found

        return df, log

    def get_tenovi_device_metric_data(
        self,
        metric_name: str,
        start_date: datetime,
        end_date: datetime,
        ) -> Tuple[pd.DataFrame, dict]:
        """
            Get all records for a metric between two dates

            Args:
                metric_name (str): The name of the metric
                start_date (datetime): The start date. None allowed.
                end_date (datetime): The end date. If None, the current date will be used.
                include_battery (bool): Include the battery percentage metric (default is False)

            Returns a tuple:
                df (pd.DataFrame): The records for the device, as a Pandas DataFrame
                log (dict): The log of the request

        """

        # deal with None start_date, end_date
        if start_date is None:
            start_date = datetime(2000)

        if end_date is None:
            end_date = datetime.now()

        # run query
        try:
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                query = f"""
                    SELECT device_name, metric_name, value_1, value_2, timestamp_local
                        FROM tenovi_raw_measurements
                        WHERE syntrillo_internal_key = %s
                            AND metric_name = %s
                            AND ( timestamp_local BETWEEN %s AND %s )
                        ORDER BY timestamp_local ASC
                """
                cursor.execute(
                    query,
                    (
                        self.syntrillo_internal_key.bytes,
                        metric_name,
                        start_date.isoformat(), end_date.isoformat() # using isoformat everywhere, to select base on local time, and not rely on mySQL time features
                     )
                )
                records = cursor.fetchall()  # Fetch all records
                log = {
                    "success": True,
                }
        except pymysql.MySQLError as e:
            log = {
                "success": False,
                "error": str(e)
            }
            records = None

        # Check if records are found
        if records:
            df = pd.DataFrame(records)
            # convert timestamp_local to datetime from isoformat
            df['timestamp_local'] = pd.to_datetime(df['timestamp_local'])
        else:
            df = pd.DataFrame()  # Return an empty DataFrame if no records found

        return df, log

    def delete_records(self, device_name: str = None) -> dict:
        """
        delete all records for a given device

        Args:
            device_name (str): The name of the device. Can be None to delete all records.

        Returns:
            log (dict): The log of the request, with "success" key set to True or False
        """

        try:
            with self.conn.cursor() as cursor:
                if device_name is None:
                    cursor.execute(
                        """DELETE FROM tenovi_raw_measurements
                        WHERE syntrillo_internal_key = %s""",
                        (self.syntrillo_internal_key.bytes)
                    )
                else:
                    cursor.execute(
                        """DELETE FROM tenovi_raw_measurements
                        WHERE syntrillo_internal_key = %s AND device_name = %s""",
                        (self.syntrillo_internal_key.bytes, device_name)
                    )
                self.conn.commit()
                log = {
                    "success": True
                }
        except pymysql.MySQLError as e:
            log = {
                "success": False,
                "error": str(e)
            }

        return log


    def get_days_with_extreme_bp(self, extreme_systolic_threshold: float, extreme_diastolic_threshold: float) -> List[str]:
        """
        Get the days with extreme BP for a patient
        Args:
            extreme_systolic_threshold (float): The systolic threshold
            extreme_diastolic_threshold (float): The diastolic threshold
        Returns:
            list[str]: The days with extreme BP
        """
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT DISTINCT date(substr(timestamp_local, 1, 10)) AS adjusted_date
                    FROM tenovi_raw_measurements
                    WHERE syntrillo_internal_key = UUID_TO_BIN(%s)
                        AND metric_name = 'blood_pressure'
                        AND (value_1 > %s OR value_2 < %s)
                    ORDER BY adjusted_date DESC
                """
                cursor.execute(
                    query,
                    (self.syntrillo_internal_key, extreme_systolic_threshold, extreme_diastolic_threshold)
                )
                records = cursor.fetchall()
                log = {
                    "success": True,
                }
        except pymysql.MySQLError as e:
            log = {
                "success": False,
                "error": str(e)
            }
            records = None

        return records, log


    def get_average_systolic_bp_over_time_period(self, number_of_days: int) -> Tuple[float, int, dict]:
        """
        Get the average systolic BP over a period if readings exist for every day in that period.

        Checks if there are blood pressure readings for every day in the specified number
        of days ending today. If so, calculates and returns the average systolic pressure
        (value_1) across all readings in that period. If any day is missing readings,
        returns -1.

        Args:
            number_of_days (int): The number of days to check, ending today (inclusive). Must be >= 1.

        Returns:
            Tuple[float, int, dict]: The average systolic BP, total number of measurements, and log
        """
        if number_of_days < 1:
            return -1, 0, {"success": False, "error": "number_of_days must be at least 1"}

        today_date = datetime.now().date()
        start_date = today_date - timedelta(days=number_of_days - 1)

        try:
            with self.conn.cursor() as cursor:
                # Query 1: Get count of distinct days with readings in the period
                query_days = """
                    SELECT COUNT(DISTINCT DATE(timestamp_local))
                    FROM tenovi_raw_measurements
                    WHERE syntrillo_internal_key = UUID_TO_BIN(%s)
                        AND metric_name = 'blood_pressure'
                        AND DATE(timestamp_local) BETWEEN %s AND %s
                """
                cursor.execute(query_days, (self.syntrillo_internal_key, start_date, today_date))
                result_days = cursor.fetchone()
                distinct_days_count = result_days[0]

                # Check if data exists for every day
                if distinct_days_count < number_of_days:
                    log = {"success": True, "message": f"Data missing for {number_of_days - distinct_days_count} day(s) in the period. distinct_days_count: {distinct_days_count}, number_of_days: {number_of_days}"}
                    return -1, 0, log

                # Query 2: Get average systolic BP and total measurement count
                query_readings = """
                    SELECT
                        AVG(value_1) as tenovi_average_systolic_bp,
                        COUNT(*) as total_measurements
                    FROM tenovi_raw_measurements
                    WHERE syntrillo_internal_key = UUID_TO_BIN(%s)
                        AND metric_name = 'blood_pressure'
                        AND DATE(timestamp_local) BETWEEN %s AND %s
                """
                cursor.execute(query_readings, (self.syntrillo_internal_key, start_date, today_date))
                result = cursor.fetchone()
                average_systolic_bp = result[0]
                total_measurements = result[1]

                if not average_systolic_bp: # Should not happen if distinct_days_count > 0, but check anyway
                    log = {"success": True, "message": "No readings found despite distinct days count."}
                    return -1, 0, log

                log = {"success": True}
                return average_systolic_bp, total_measurements, log

        except pymysql.MySQLError as e:
            log = {
                "success": False,
                "error": f"Database error: {str(e)}"
            }
            return -1, 0, log
        except Exception as e:
            log = {
                "success": False,
                "error": f"Calculation error: {str(e)}"
            }
            return -1, 0, log


    def get_all_patient_bp_data_by_syntrillo_internal_key(self, syntrillo_internal_key: str) -> Tuple[list[str], dict]:
        """
        Retrieves all dates which have at least one BP measurement for a given patient.

        Args:
            syntrillo_internal_key (str): The Syntrillo internal key
        Returns:
            list[str]: The dates with at least one BP measurement
        """
        logger.info(f"Getting BP data for patient with syntrillo_internal_key {syntrillo_internal_key}")
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT DISTINCT substr(timestamp_local, 1, 10) AS adjusted_date
                        FROM tenovi_raw_measurements
                        WHERE syntrillo_internal_key = UUID_TO_BIN(%s)
                            AND metric_name = 'blood_pressure'
                        ORDER BY adjusted_date DESC
                """
                cursor.execute(query, (syntrillo_internal_key))
                records = cursor.fetchall()
                all_dates_response = []
                for record in records:
                    all_dates_response.extend(record)

                log = {"success": True }
                logger.info(f"BP data for patient with syntrillo_internal_key {syntrillo_internal_key} retrieved successfully")

        except pymysql.MySQLError as e:
            logger.error(f"ERROR: error getting BP data for patient with syntrillo_internal_key.")
            log = {
                "success": False,
                "error": str(e)
            }
            all_dates_response = None

        return all_dates_response, log

    def get_all_internal_keys(self):

        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT DISTINCT syntrillo_internal_key
                    FROM tenovi_raw_measurements;
                """

                cursor.execute(query)
                raw_keys = cursor.fetchall()
                internal_keys = []
                for key in raw_keys:
                    internal_keys.extend(key)

                log = {"success": True }
                logger.info(f"Successfully retrieved Syntrillo internal keys!")

        except pymysql.MySQLError as e:
            logger.error(f"Error retrieving syntrillo_internal_key's.")
            log = {
                "success": False,
                "error": str(e)
            }
            internal_keys = None

        return internal_keys, log

    def get_latest_measurements(self, metric_name: str, count: int = None) -> Tuple[list[dict], dict]:
        """
        Returns specific number of measurements

        Args:
            metric_name (str): The name of the metric to retrieve
            count (int): The number of measurements to retrieve (optional)

        Returns:
            measurements (list[dict]): The measurements
            log (dict): The log of the request, with "success" key set to True or False

        """

        try:
            with self.conn.cursor() as cursor:
                # Determine the metric filter
                if (not metric_name == BLOOD_PRESSURE_METRIC_NAME) and (not metric_name == PULSE_METRIC_NAME): # Blood Pressure data
                    metric_name = "1=1"  # No filter if metric_name is not recognized

                query = f"""
                    SELECT value_1, value_2, timestamp_local as timestamp
                    FROM tenovi_raw_measurements
                    WHERE metric_name = %s AND syntrillo_internal_key = %s
                    ORDER BY timestamp_local DESC
                """
                # If count is provided, add it to the query
                if count:
                    query += " LIMIT %s"
                    cursor.execute(query, (metric_name, self.syntrillo_internal_key.bytes, count))
                else:
                    cursor.execute(query, (metric_name, self.syntrillo_internal_key.bytes))

                rows = cursor.fetchall()
                # Convert to list of dicts
                measurements = [
                    {'value_1': row[0], 'value_2': row[1], 'timestamp': row[2]} for row in rows
                ]
                log = {"success": True}

        except pymysql.MySQLError as e:
            logger.error(f"Error retrieving syntrillo_internal_key's: {e}")
            log = {
                "success": False,
                "error": str(e)
            }
            measurements = None

        return measurements, log

    def get_srs_form_responses(self, syntrillo_internal_key_patient: uuid.UUID) -> Tuple[list[SRSFormResponse], dict]:
        """
        Retrieves all the SRS form responses for a given patient from the srs_form_responses table

        Args:
            syntrillo_internal_key_patient (uuid.UUID): The Syntrillo internal key

        Returns:
            srs_form_responses (list[SRSFormResponse]): The SRS form responses
        Raises:
            pymysql.MySQLError: If there is an error retrieving the SRS form responses.
            Exception: If there is an unexpected error during the retrieval.
        """
        logger.info(f"Retrieving SRS form responses for patient with syntrillo_internal_key {syntrillo_internal_key_patient} ...")

        try:
            syntrillo_internal_key_patient_str = str(syntrillo_internal_key_patient) # Id is stored as a string in the database
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                query = """
                    SELECT
                        sfr.*,
                        sc.strokeCompliance,
                        sc.tiaCompliance,
                        sc.chronicInfarctCompliance,
                        sc.atrialFibrillationCompliance,
                        sc.ironDeficiencyAnemiaCompliance,
                        sc.arterialClotsCompliance,
                        sc.venousClotsCompliance,
                        sc.chfCompliance,
                        sc.carotidStenosisCompliance,
                        sc.osaCompliance,
                        sc.cadCompliance,
                        sc.valvularHeartDiseaseCompliance,
                        sc.ckdCompliance,
                        sc.pfoCompliance
                    FROM
                        srs_form_responses AS sfr
                    LEFT JOIN
                        srs_compliance_records AS sc ON sfr.srs_form_response_id = sc.srs_form_response_id
                    WHERE
                        sfr.syntrillo_internal_key_patient = %s
                    ORDER BY
                        sfr.created_at DESC;
                """
                cursor.execute(query, (syntrillo_internal_key_patient_str,))
                rows = cursor.fetchall()

                srs_form_responses = []
                for row in rows:
                    # The row contains all fields needed for SRSFormResponse,
                    # and Pydantic will ignore extra fields.
                    form_response = SRSFormResponse.model_validate(row)

                    # Check if there is any compliance data from the LEFT JOIN.
                    if row.get('strokeCompliance') is not None:
                        # The row also contains all fields for TreatmentCompliance.
                        compliance_obj = TreatmentCompliance.model_validate(row)
                        form_response.compliance = compliance_obj

                    srs_form_responses.append(form_response)

                log = {"success": True}
                return srs_form_responses

        except pymysql.MySQLError as e:
            log = {
                "success": False,
                "error": str(e)
            }
            return None

        except Exception as e:
            log = {
                "success": False,
                "error": str(e)
            }
            return None


    def insert_srs_form_response(self, srs_form_response: SRSFormResponse) -> Tuple[Optional[int], dict]:
        """
        Insert the SRS form response and associated compliance data into the database.

        Args:
            srs_form_response (SRSFormResponse): The SRS form response data model.

        Returns:
            A tuple containing:
                - Optional[int]: The ID of the newly created SRS form response, or None on failure.
                - dict: A log dictionary.
        Raises:
            pymysql.MySQLError: If there is an error inserting the SRS form response.
            Exception: If there is an unexpected error during the insertion.
        """
        logger.info(f"Performing insertion of SRS form response into RDS DB ...")
        print(f"Performing insertion of SRS form response into RDS DB ...")
        # Exclude the compliance and srs_form_response_id fields from the form data for srs response insertion.
        form_data = srs_form_response.model_dump(exclude={'compliance', 'srs_form_response_id'}, exclude_none=True)
        # Extract the compliance data from the SRS form response.
        compliance_data = srs_form_response.compliance

        try:
            self.conn.begin()  # Start a transaction

            with self.conn.cursor() as cursor:
                # 1. Insert into srs_form_responses
                form_columns = ', '.join(form_data.keys())
                form_placeholders = ', '.join(['%s'] * len(form_data))
                form_query = f"""
                    INSERT INTO srs_form_responses ({form_columns})
                    VALUES ({form_placeholders});
                """
                cursor.execute(form_query, list(form_data.values()))

                # Get the ID of the new record
                srs_form_response_id = cursor.lastrowid
                logger.info(f"Successfully inserted into srs_form_responses with ID: {srs_form_response_id}")
                print(f"Successfully inserted into srs_form_responses with ID: {srs_form_response_id}")

                # 2. Insert into srs_compliance if compliance data exists
                if compliance_data:
                    logger.info(f"Performing insertion of compliance data into RDS DB ...")

                    compliance_dict = compliance_data.model_dump(exclude_none=True)
                    compliance_dict['srs_form_response_id'] = srs_form_response_id

                    compliance_columns = ', '.join(compliance_dict.keys())
                    compliance_placeholders = ', '.join(['%s'] * len(compliance_dict))
                    compliance_query = f"""
                        INSERT INTO srs_compliance_records ({compliance_columns})
                        VALUES ({compliance_placeholders});
                    """
                    cursor.execute(compliance_query, list(compliance_dict.values()))
                    logger.info(f"Successfully inserted compliance data into RDS DB for response ID: {srs_form_response_id}")

            self.conn.commit()  # Commit the transaction
            log = {"success": True}
            return srs_form_response_id, log

        except pymysql.MySQLError as e:
            self.conn.rollback()  # Rollback insertion transaction on error
            log = {
                "success": False,
                "error": str(e)
            }
            print(f"Error inserting SRS form response: {e}")
            logger.error(f"Error inserting SRS form response: {e}")
            return None, log

        except Exception as e:
            self.conn.rollback()  # Rollback insertion transaction on error
            log = {
                "success": False,
                "error": f"An unexpected error occurred: {e}"
            }
            print(f"An unexpected error occurred during SRS form insertion: {e}")
            logger.error(f"An unexpected error occurred during SRS form insertion: {e}")
            return None, log


    def get_form_module_ids_by_module_label(self, module_label: str) -> Tuple[str, str]:
        """
        Get the form and module ids for a given module label.

        Args:
            module_label (str): The module label to query by.

        Returns:
            form_id (str): The form id associated with the module label.
            module_id (str): The module id associated with the module label.
        Raises:
            pymysql.MySQLError: If there is an error retrieving the form and module ids.
            Exception: If there is an unexpected error during the retrieval.
        """
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT form_id, module_id
                    FROM module_label_look_up
                    WHERE module_label = %s;
                """
                cursor.execute(query, (module_label,))
                form_id, module_id = cursor.fetchone()

                return form_id, module_id

        except pymysql.MySQLError as e:
            log = {
                "success": False,
                "error": str(e)
            }
            return None, None

        except Exception as e:
            log = {
                "success": False,
                "error": f"An unexpected error occurred: {e}"
            }
            return None, None

    def get_patient_form_response_by_module_id(self, module_id: str, syntrillo_internal_key: str) -> str:
        """
        Get the form and module ids for a given module id.

        Args:
            module_id (str): The module id to query by.
            syntrillo_internal_key (str): The syntrillo internal key to query by.
        Returns:
            answer (str): The answer to the question.
            created_at (str): The timestamp of the answer.
        Raises:
            pymysql.MySQLError: If there is an error retrieving the form and module ids.
            Exception: If there is an unexpected error during the retrieval.
        """
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT
                        answer,
                        created_at
                    FROM
                        healthie_form_responses
                    WHERE module_id = %s AND syntrillo_internal_key = %s
                    ORDER BY created_at DESC;
                """
                cursor.execute(query, (module_id, syntrillo_internal_key))
                answer, created_at = cursor.fetchone()

                return answer, created_at

        except pymysql.MySQLError as e:
            log = {
                "success": False,
                "error": str(e)
            }
            return None, None

        except Exception as e:
            log = {
                "success": False,
                "error": f"An unexpected error occurred: {e}"
            }
            return None, None

    def get_srs_value_by_category_and_value(self, category: str, value: Union[float, str] = None) -> dict:
        """
        Gets the SRS value assoicated with the risk factor's value.

        Args:
            category (str): The category of the risk factor.
            value (float | str): The value of the risk factor.

        Returns:
            dict: The SRS value and the stroke priority value.
        Raises:
            ValueError: If the value type is invalid.
        """

        try:
            with self.conn.cursor() as cursor:
                if value:
                    if type(value) == str:
                        query = """
                            SELECT risk_value
                            FROM srs_independent_risk_values
                            WHERE category = %s AND categorical_value = %s;
                        """
                        variables = (category, value)
                    elif type(value) == float:
                        query = """
                            SELECT risk_value
                            FROM srs_independent_risk_values
                            WHERE category = %s AND min_value <= %s AND max_value >= %s;
                        """
                        variables = (category, value, value)
                    else:
                        raise ValueError(f"Invalid value type: {type(value)}")
                else:
                    query = """
                        SELECT risk_value
                        FROM srs_independent_risk_values
                        WHERE category = %s AND is_default = 1;
                    """
                    query_stroke_priority = """
                        SELECT max(risk_value)
                        FROM srs_independent_risk_values
                        WHERE category = %s;
                    """
                    variables = (category)

                cursor.execute(query, variables)
                risk_value = cursor.fetchone()

                stroke_priority_value = risk_value
                if not value:
                    cursor.execute(query_stroke_priority, variables)
                    stroke_priority_value = cursor.fetchone()

                risk_values = {
                    "risk_value": risk_value[0] if risk_value else 0.0,
                    "stroke_priority_value": stroke_priority_value[0] if stroke_priority_value else 0.0
                }

                return risk_values

        except pymysql.MySQLError as e:
            log = {
                "success": False,
                "error": str(e)
            }
            return log

        except Exception as e:
            log = {
                "success": False,
                "error": f"An unexpected error occurred: {e}"
            }
            return log




if __name__ == '__main__':

    lookup_codes = LookUpCodesManagement()
    entry = lookup_codes.retrieve_entry_by_healthie_user_id('1051529') # 1051529 : Omar's "Patient One"

    data_manager = SyntrilloDatabaseManager(entry['syntrillo_internal_key'])

    if False:
        record, log = data_manager.get_latest_record_for_tenovi_device("Tenovi Watch")
        print(record, log)

    if False:
        report, log = data_manager.get_summary_devices_report()
        # Pretty print the report
        print(log)
        print(json.dumps(report, indent=4))

    if False:
        records, log = data_manager.get_blood_pressure_records_after_local_timestamp(None)
        # Pretty print the records
        print(log)
        print(records)

    if False:
        log = data_manager.delete_records(None)
        print(log)

    if False:
        records, log = data_manager.get_daily_stats_metric_records_after_local_timestamp(None, "steps")
        # Pretty print the records
        print(log)
        print(json.dumps(records, indent=4, default=str))

    if True:
        today = datetime.now().date()
        df, log = data_manager.get_tenovi_device_data("Tenovi Pillbox", datetime(2024, 1, 1), today)

        print(log)
        print(df)

    if False: # Test block for SRS form insertion
        print("\n--- Testing SRS Form Insertion ---")

        try:
            # 1. Create dummy data for TreatmentCompliance.
            # A dummy srs_form_response_id is required to satisfy the Pydantic model.
            # The actual ID will be generated and overwritten by the insertion logic.
            dummy_compliance = TreatmentCompliance(
                srs_form_response_id=0,
                strokeCompliance="optimized",
                tiaCompliance="partially optimized",
                chronicInfarctCompliance="not optimized",
                atrialFibrillationCompliance="optimized",
                ironDeficiencyAnemiaCompliance="partially optimized",
                arterialClotsCompliance="not optimized",
                venousClotsCompliance="optimized",
                chfCompliance="partially optimized",
                carotidStenosisCompliance="not optimized",
                osaCompliance="optimized",
                cadCompliance="partially optimized",
                valvularHeartDiseaseCompliance="not optimized",
                ckdCompliance="optimized",
                pfoCompliance="partially optimized"
            )

            # 2. Create dummy data for the main SRSFormResponse.
            dummy_form_response = SRSFormResponse(
                syntrillo_internal_key_patient=str(entry['syntrillo_internal_key']),
                syntrillo_internal_key_clinician=str(uuid.uuid4()),
                created_at=datetime.now(),
                HasPreviousStroke=True,
                NumberOfStrokes="Multiple",
                LatestStrokeMechanism="Large Vessel",
                ScreenedForTIA=True,
                LikelihoodOfTIA="High Likelihood",
                Weight=175.5,
                Height="5'11\"",
                BMI=24.5,
                compliance=dummy_compliance  # Nest the compliance object
            )

            # 3. Call the insertion function.
            print("Attempting to insert the following data:")
            print(dummy_form_response.model_dump_json(indent=2))

            new_id, log = data_manager.insert_srs_form_response(dummy_form_response)

            # 4. Print the results.
            print(f"\nInsertion Log: {log}")
            if log.get('success'):
                print(f"✅ Successfully inserted new SRS form response with ID: {new_id}")
            else:
                print(f"❌ Insertion failed.")

        except Exception as e:
            print(f"An error occurred during the test setup: {e}")
            import traceback
            traceback.print_exc()

        print("--- End of SRS Form Insertion Test ---\n")
