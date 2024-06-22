
import uuid
import json
import pymysql
from typing import Tuple

from syntrillo.databases_management.connection import DatabaseConnection
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement

class SyntrilloDatabaseManager:

    # Tenovi devices
    TENOVI_DEVICE_NAMES=[
        "Tenovi Watch",
        "Tenovi Pillbox",
        "Tenovi BPM - L",
        "Tenovi BPM - S"
        ]


    def __init__(
        self,
        syntrillo_internal_key : uuid.UUID, # TODO : make sure all syntrillo_internal_key are uuid.UUID
        ):
        """
            For a given patient, manage data located in our Syntrillo PHI database
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
            Get the latest timestamp for a given device

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
                    "SELECT * FROM tenovi_raw_measurements WHERE device_name = %s ORDER BY timestamp_zulu DESC LIMIT 1",
                    (device_name,)
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
        ):
        """
            Insert a new raw measurement for a Tenovi device
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
                    (self.syntrillo_internal_key, device_name, metric_name, value_1, value_2, timestamp_zulu, data_json)
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


if __name__ == '__main__':

    lookup_codes = LookUpCodesManagement()
    entry = lookup_codes.retrieve_entry_by_healthie_user_id('1051529') # 1051529 : Omar's "Patient One"

    data_manager = SyntrilloDatabaseManager(entry['syntrillo_internal_key'])

    record, log = data_manager.get_latest_record_for_tenovi_device("Tenovi Watch")

    print(record, log)

