# Path: ./sources/syntrillo/remote_monitoring/syntrillo_medications_db_manager.py

import uuid
import pymysql
from typing import Tuple, List, Dict, Any, Optional
from enum import Enum as PyEnum
from datetime import datetime, date
import json
from pymysql.cursors import DictCursor

from syntrillo.medications.models import MedicationRecord
from syntrillo.databases_management.connection import DatabaseConnection
from syntrillo.system.logger import logger


class SyntrilloMedicationsDatabaseQueries:
    """
    A class to manage remote monitoring data in the Syntrillo PHI database.
    Specifically any DB operations dealing with medications information.
    """

    MED_DB_COLUMN_NAMES = [
        # matches the column order in create-or-recreate-tables.sql
        'medication_record_id',
        'medication_name',
        'medication_id',
        'is_active',
        'created_at',
        'updated_at',
        'dosage_option_id',
        'start_date',
        'end_date',
        'comment',
        'directions',
        'mirrored',
        'syntrillo_internal_key',
        'common_medication_id',
        'delivery_method',
        'dosing_schedule_rule',
        'total_daily_dose',
        'dosage_amount',
        'dosage_unit',
        'dose_count',
        'frequency',
        'dosing_interval',
        'time_of_day',
        'day_period',
        'day_of_week',
        'pinned'
    ]

    def __init__(self) -> None:
        """
        For a given patient, manage data located in our Syntrillo PHI database

        Args:
            None
        Returns:
            None
        """
        # connect to our database
        db_conn = DatabaseConnection(DatabaseConnection.HEALTH_INFO_DB)
        self.conn, _ = db_conn.create_connection()
        logger.info(f"DB connection info: host={getattr(self.conn,'host',None)} port={getattr(self.conn,'port',None)} user={getattr(self.conn,'user',None)} db={getattr(self.conn,'db',None)} autocommit={self.conn.get_autocommit() if hasattr(self.conn,'get_autocommit') else 'unknown'}")

    def get_similar_medication_names(self, partial_name: str) -> List[str]:
        """
        Fetches a list of medication names from the medications_records table
        that are similar to the provided partial name.

        Args:
            partial_name (str): The partial medication name to search for.
        Returns:
            List[str]: A list of similar medication names.
        """
        try:
            with self.conn.cursor() as cursor:
                # Using parameterized query to prevent SQL injection
                query = """
                    SELECT id, common_name, category, supercategory, category_custom, supercategory_custom
                    FROM common_medications
                    WHERE common_name LIKE %s;
                """
                like_pattern = f"%{partial_name}%"
                cursor.execute(query, (like_pattern,))
                results = cursor.fetchall()
                print(results)
                normalized_results = []
                for row in results:
                    normalized_results.append({
                        "id": row[0],
                        "common_name": row[1],
                        "category": row[2],
                        "supercategory": row[3],
                        "category_custom": row[4],
                        "supercategory_custom": row[5],
                    })

            logger.info(f"Fetched {len(normalized_results)} similar medication names for partial name: '{partial_name}'")
            return normalized_results

        except Exception as e:
            logger.error(f"An error occurred while fetching similar medication names: {e}")
            return []

    def get_patient_medications(self, syntrillo_internal_key: str) -> Tuple[Dict[int, Dict[str, Any]], dict]:
        """
        Fetches and structures medication records for a patient.

        The records are grouped by medication_id, with the most recent record
        separated from its historical versions.

        Args:
            syntrillo_internal_key (str): Internal patient identifier.

        Returns:
            medications_data (Dict[int, Dict[str, Any]]): A dictionary where keys are medication_ids.
                                    Each value contains the 'current' record
                                    and a 'history' list of older records.
            log (dict): The logs for the DB operation.
        """
        medications_data = {}

        try:
            with self.conn.cursor(DictCursor) as cursor:
                query = """
                    SELECT *
                    FROM patient_medications
                    WHERE syntrillo_internal_key = %s
                    ORDER BY created_at ASC;
                """
                cursor.execute(query, (syntrillo_internal_key,))
                records = cursor.fetchall()

                for record in records:
                    id = record['id']
                    common_medication_id = record['common_medication_id']

                    # Fetch common medication details
                    common_med_query = """
                        SELECT *
                        FROM common_medications
                        WHERE id = %s;
                    """
                    cursor.execute(common_med_query, (common_medication_id,))
                    common_med = cursor.fetchone()

                    if common_med:
                        common_med.pop('created_at', None)
                        common_med.pop('id', None)
                        record = {**record, **common_med}

                    # Convert JSON strings to lists
                    if record.get('day_period'):
                        record['day_period'] = json.loads(record['day_period'])
                    if record.get('day_of_week'):
                        record['day_of_week'] = json.loads(record['day_of_week'])

                    # Convert timedelta to string
                    from datetime import timedelta
                    if record.get('time_of_day') and isinstance(record['time_of_day'], timedelta):
                        total_seconds = int(record['time_of_day'].total_seconds())
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        seconds = total_seconds % 60
                        record['time_of_day'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                    # Convert datetime/date objects to strings
                    for key, value in record.items():
                        if isinstance(value, datetime):
                            record[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                        elif isinstance(value, date):
                            record[key] = value.strftime('%Y-%m-%d')

                    medications_data[id] = record

            log = {"success": True, "error": None}
            return medications_data, log

        except Exception as e:
            self.conn.rollback()
            logger.error(f"An error occurred: {e}")
            log = {"success": False, "error": str(e)}
            return {}, log

    def get_medication_record_by_id(self, medication_id: str) -> Tuple[Optional[Dict[str, Any]], dict]:
        """
        Fetches a single medication record by its unique identifier.

        Args:
            medication_id (str): The unique identifier of the medication record.
        Returns:
            Tuple[Optional[Dict[str, Any]], dict]: A tuple containing the medication record as a dictionary
                                                   (or None if not found) and a log dictionary.
        """
        try:
            with self.conn.cursor(DictCursor) as cursor:
                query = """
                    SELECT *
                    FROM patient_medications
                    WHERE id = %s;
                """
                cursor.execute(query, (medication_id,))
                record = cursor.fetchone()  # Fetches the row as a dict

                if not record:
                    return None, {"success": False, "error": f"Medication record {medication_id} not found"}

                # Convert JSON strings back to lists
                if record.get('day_period'):
                    record['day_period'] = json.loads(record['day_period'])
                if record.get('day_of_week'):
                    record['day_of_week'] = json.loads(record['day_of_week'])

                # Convert timedelta to string (HH:MM:SS format)
                from datetime import timedelta
                if record.get('time_of_day') and isinstance(record['time_of_day'], timedelta):
                    total_seconds = int(record['time_of_day'].total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    record['time_of_day'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                # Convert datetime objects to strings
                for key, value in record.items():
                    if isinstance(value, datetime):
                        record[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                    elif isinstance(value, date):
                        record[key] = value.strftime('%Y-%m-%d')

                # Fetch common medication details if available
                if record.get('common_medication_id'):
                    common_med_query = """
                        SELECT *
                        FROM common_medications
                        WHERE id = %s;
                    """
                    cursor.execute(common_med_query, (record['common_medication_id'],))
                    common_med = cursor.fetchone()

                    if common_med:
                        common_med.pop('created_at', None)  # remove unneeded field
                        common_med.pop('id', None)  # remove unneeded field
                        record = {**record, **common_med}

            log = {"success": True, "error": None}
            return record, log

        except Exception as e:
            logger.error(f"An error occurred while fetching medication record ID {medication_id}: {e}")
            log = {"success": False, "error": str(e)}
            return None, log

    def insert_common_medication(self, common_medication) -> Tuple[Optional[int], dict]:
        """
        Insert a record taken from the Medications form into the common_medications table in DB.

        Args:
            common_medication (CommonMedication): The common medication object with needed information.
        Returns
            Tuple[Optional[int], dict]
        """
        data = common_medication.model_dump(exclude_none=True)
        logger.info(f"Creating common medication for medication name: {common_medication.common_name}")
        try:
            self.conn.begin()

            with self.conn.cursor() as cursor:
                # Get DB column names based on CommonMedication object keys
                cols = ", ".join(data.keys())
                placeholders = ", ".join(["%s"] * len(data))
                sql = f"""
                    INSERT INTO common_medications ({cols})
                    VALUES ({placeholders});
                """
                cursor.execute(sql, list(data.values()))
                new_id = cursor.lastrowid

            self.conn.commit()

            log = {"success": True, "error": None}
            logger.info(f"Successfully updated common medication record in internal DB...")
            return new_id, log

        except pymysql.MySQLError as e:
            self.conn.rollback()
            log = {"success": False, "error": str(e)}
            logger.error("Error while updating common medication record in internal DB...")
            return None, log

        except Exception as e:
            self.conn.rollback()
            log = {"success": False, "error": str(e)}
            logger.error("Error while updating common medication record in internal DB...")
            return None, log

    def insert_patient_medication(self, medication_record: MedicationRecord) -> Tuple[dict, dict]:
        """
        Insert a record taken from the Medications form into the medications_records table in DB.

        Args:
            medication_record (MedicationRecord): The medication record object with needed information.
        Returns
            Tuple[Optional[int], dict]
        """
        data = medication_record.model_dump(exclude_none=True)
        # logger.info(f"Creating medication for medication id: {medication_record.medication_id}")
        # print("data:", data)

        processed = {}
        for k, v in data.items():
            if isinstance(v, PyEnum):
                processed[k] = v.value
            elif isinstance(v, (list, dict)):
                # empty lists -> store as JSON '[]'
                processed[k] = json.dumps(v)
            elif isinstance(v, datetime):
                # strip timezone, MySQL TIMESTAMP/TIMESTAMPTZ handling depends on server
                processed[k] = v.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(v, date):
                processed[k] = v.strftime('%Y-%m-%d')
            else:
                processed[k] = v

        try:
            # self.conn.begin()
            logger.info(f"Inserting medication record into DB for medication: {medication_record}")
            with self.conn.cursor() as cursor:
                # Use processed keys (the exact values we're sending) to build columns/placeholders
                cols = ", ".join(processed.keys())
                placeholders = ", ".join(["%s"] * len(processed))
                sql = f"INSERT INTO patient_medications ({cols}) VALUES ({placeholders});"
                logger.info(f"Executing SQL: {sql} | cols: {cols} | params: {placeholders}")
                cursor.execute(sql, list(processed.values()))
                self.conn.commit()

            new_record, log = self.get_medication_record_by_id(medication_record.id)

            log = {"success": True, "error": None}
            logger.info("Successfully inserted medication record in internal DB...")
            return new_record, log

        except pymysql.MySQLError as e:
            self.conn.rollback()
            log = {"success": False, "error": str(e)}
            logger.error("Error while updating medication record in internal DB...")
            return None, log

        except Exception as e:
            self.conn.rollback()
            log = {"success": False, "error": str(e)}
            logger.error("Error while updating medication record in internal DB...")
            return None, log

    def update_patient_medication(self, id: int, updated_fields: Dict[str, Any]) -> Tuple[bool, dict]:
        """
        Update specific fields of a medication record in the medications_records table.

        Args:
            id (int): The unique identifier of the medication record to update.
            updated_fields (Dict[str, Any]): A dictionary of fields to update with their new values.
        Returns:
            Tuple[bool, dict]: A tuple containing a boolean indicating success (True) or failure (False),
                               and a log dictionary with operation details.
        """

        if not updated_fields:
            return None, {"success": False, "error": "No fields to update"}

        # Process the values before building the SQL
        processed_fields = {}
        for key, value in updated_fields.items():
            if isinstance(value, PyEnum):
                processed_fields[key] = value.value
            elif isinstance(value, (list, dict)):
                # Convert lists/dicts to JSON strings
                processed_fields[key] = json.dumps(value)
            elif isinstance(value, datetime):
                processed_fields[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(value, date):
                processed_fields[key] = value.strftime('%Y-%m-%d')
            elif value is None:
                processed_fields[key] = None
            else:
                processed_fields[key] = value

        try:
            with self.conn.cursor() as cursor:
                # Build the SET clause
                set_clause = ", ".join([f"{key} = %s" for key in processed_fields.keys()])
                sql = f"""
                    UPDATE patient_medications
                    SET {set_clause}
                    WHERE id = %s;
                """

                # Values for the query (processed values + id)
                values = list(processed_fields.values()) + [id]

                logger.info(f"Executing SQL: {sql} | params: {values}")
                cursor.execute(sql, values)

            self.conn.commit()
            logger.info(f"Successfully updated medication record ID {id}")

            # Fetch the updated record
            updated_record, fetch_log = self.get_medication_record_by_id(id)

            if not fetch_log['success']:
                logger.error(f"Failed to fetch updated medication ID {id}: {fetch_log['error']}")
                return None, fetch_log

            log = {"success": True, "error": None}
            return updated_record, log

        except pymysql.MySQLError as e:
            self.conn.rollback()
            log = {"success": False, "error": str(e)}
            logger.error(f"Error while updating medication record ID {id} in internal DB...")
            return False, log

        except Exception as e:
            self.conn.rollback()
            log = {"success": False, "error": str(e)}
            logger.error(f"Error while updating medication record ID {id} in internal DB...")
            return False, log

    def delete_patient_medication(self, medication_id: str) -> Tuple[bool, dict]:
        """
        Deletes ALL records associated with a given medication_id.

        This function removes all historical and current entries for a specific
        medication from the medications_records table.

        Args:
            medication_id (str): The unique identifier for the medication to be deleted.
        Returns:
            Tuple[bool, dict]: A tuple containing a boolean indicating success (True) or failure (False),
                               and a log dictionary with operation details.
        """
        logger.info(f"Attempting to delete all records for medication_id: {medication_id}")
        try:
            # Begin a transaction to ensure atomicity
            self.conn.begin()
            with self.conn.cursor() as cursor:

                query = "DELETE FROM patient_medications WHERE id = %s"
                # The execute method returns the number of affected rows
                rows_affected = cursor.execute(query, (medication_id,))

            # Commit the transaction to make the deletion permanent
            self.conn.commit()

            if rows_affected > 0:
                logger.info(f"Successfully deleted {rows_affected} records for medication_id: {medication_id}")
            else:
                logger.warning(f"No records found to delete for medication_id: {medication_id}. Operation successful.")

            log = {
                "success": True,
                "error": None,
                "rows_affected": rows_affected
            }
            return True, log

        except pymysql.MySQLError as e:
            # Rollback the transaction in case of a database-specific error
            self.conn.rollback()
            log = {
                "success": False,
                "error": f"MySQL Error: {e}"
            }
            logger.error(f"Failed to delete records for medication_id {medication_id} due to a database error.")
            return False, log

        except Exception as e:
            # Rollback the transaction for any other unexpected errors
            self.conn.rollback()
            log = {
                "success": False,
                "error": str(e)
            }
            logger.error(f"An unexpected error occurred while deleting records for medication_id {medication_id}.")
            return False, log
