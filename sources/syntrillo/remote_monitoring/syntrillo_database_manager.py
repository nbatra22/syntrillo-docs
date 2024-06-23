
import uuid
import json
import pymysql
from typing import Tuple

from syntrillo.databases_management.connection import DatabaseConnection
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
import json

class SyntrilloDatabaseManager:
    """
    A class to manage remote monitoring data in the Syntrillo PHI database.

    Attributes:
       TENOVI_DEVICE_NAMES : list, with valid Tenovi device names

    """

    # Tenovi devices
    TENOVI_DEVICE_NAMES=[
        "Tenovi Watch",
        "Tenovi Pillbox",
        "Tenovi BPM - L",
        "Tenovi BPM - S"
        ]


    def __init__(
        self,
        syntrillo_internal_key: uuid.UUID,
        ):
        """
            For a given patient, manage data located in our Syntrillo PHI database

            Args:
                syntrillo_internal_key (uuid.UUID): The internal key for the patient
        """

        self.syntrillo_internal_key = syntrillo_internal_key

        # connect to our database
        db_conn = DatabaseConnection(DatabaseConnection.HEALTH_INFO_DB)
        self.conn, _ = db_conn.create_connection()

    def get_latest_record_for_tenovi_device(
        self,
        device_name: str
        ) -> Tuple[dict, dict]:
        """
            Get the latest record for a given device.

            Used to get the latest timestamp for a device to sync data from Tenovi to Healthie.

            Args:
                device_name (str): The name of the device

            Returns a tuple:
                record (dict): The latest record for the device
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
                    """SELECT *
                    FROM tenovi_raw_measurements
                    WHERE syntrillo_internal_key = %s AND device_name = %s
                    ORDER BY timestamp_zulu DESC LIMIT 1""",
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
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO tenovi_raw_measurements
                    (syntrillo_internal_key, device_name, metric_name, value_1, value_2, timestamp_zulu, data_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (self.syntrillo_internal_key.bytes, device_name, metric_name, value_1, value_2, timestamp_zulu, data_json)
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

        log = {
            "success": True,
        }

        try:
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT
                        device_name,
                        COUNT(*) as number_of_data_points_in_syntrillo_database,
                        MAX(timestamp_zulu) as latest_zulu_timestamp_in_syntrillo_database
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

    def get_blood_pressure_records_after_timestamp(
        self,
        timestamp_zulu: str
        ) -> Tuple[dict, dict]:
        """
            Get all records for a device after a given timestamp.

            Args:
                device_name (str): The name of the device
                timestamp_zulu (str): The timestamp (zulu time) to filter by

            Returns a tuple:
                records (dict): The records for the device
                log (dict): The log of the request

        """

        try:
            with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
                if timestamp_zulu is None:
                    cursor.execute(
                        """
                        SELECT * FROM tenovi_raw_measurements
                        WHERE metric_name = 'blood_pressure'
                        AND syntrillo_internal_key = %s
                        ORDER BY timestamp_zulu ASC
                        """,
                        (self.syntrillo_internal_key.bytes,)
                    )
                else:
                    cursor.execute(
                        """
                        SELECT * FROM tenovi_raw_measurements
                        WHERE metric_name = 'blood_pressure'
                        AND syntrillo_internal_key = %s
                        AND timestamp_zulu > %s
                        ORDER BY timestamp_zulu ASC
                        """,
                        (self.syntrillo_internal_key.bytes, timestamp_zulu)
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


if __name__ == '__main__':

    lookup_codes = LookUpCodesManagement()
    entry = lookup_codes.retrieve_entry_by_healthie_user_id('1051529') # 1051529 : Omar's "Patient One"

    data_manager = SyntrilloDatabaseManager(entry['syntrillo_internal_key'])

    if False:
        record, log = data_manager.get_latest_record_for_tenovi_device("Tenovi Watch")
        print(record, log)

    if True:
        report, log = data_manager.get_summary_devices_report()
        # Pretty print the report
        print(log)
        print(json.dumps(report, indent=4))

    if False:
        records, log = data_manager.get_blood_pressure_records_after_timestamp(None)
        # Pretty print the records
        print(log)
        print(records)


