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
        'day_of_week'
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

    def insert_common_medication_record(self, common_medication) -> Tuple[Optional[int], dict]:
        """
        Insert a record taken from the Medications form into the common_medications table in DB.

        Args:
            common_medication (CommonMedication): The common medication object with needed information.
        Returns
            Tuple[Optional[int], dict]
        """
        data = common_medication.model_dump(exclude_none=True)
        logger.info(f"Updating common medication for medication name: {common_medication.common_name}")
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

    def insert_medication_record(self, medication_record: MedicationRecord) -> Tuple[Optional[int], dict]:
        """
        Insert a record taken from the Medications form into the medications_records table in DB.

        Args:
            medication_record (MedicationRecord): The medication record object with needed information.
        Returns
            Tuple[Optional[int], dict]
        """
        data = medication_record.model_dump(exclude_none=True)
        logger.info(f"Updating medication for medication id: {medication_record.medication_id}")
        print("data:", data)

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
            self.conn.begin()
            with self.conn.cursor() as cursor:
                # Get DB column names based on MedicationRecord object keys
                cols = ", ".join(data.keys())
                placeholders = ", ".join(["%s"] * len(data))
                sql = f"""
                    INSERT INTO medications_records ({cols})
                    VALUES ({placeholders});
                """
                # print("SQL:", sql)
                cursor.execute(sql, list(processed.values()))
                new_id = cursor.lastrowid
            # breakpoint()
            self.conn.commit()
            log = {"success": True, "error": None}
            logger.info("Successfully updated medication record in internal DB...")
            return new_id, log

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


    def get_medication_records_for_patient(self, syntrillo_internal_key: str) -> Tuple[Dict[int, Dict[str, Any]], dict]:
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
                    FROM medications_records
                    WHERE syntrillo_internal_key = %s
                    ORDER BY medication_id, created_at DESC;
                """
                cursor.execute(query, (syntrillo_internal_key,))
                records = cursor.fetchall() # Fetches all rows as a list of dicts
                print("records:", records)
                # for record_tuple in records:
                #     record_tuple = dict(zip(self.MED_DB_COLUMN_NAMES, record_tuple))
                #     # Validate and convert the raw dictionary into a Pydantic model
                #     record_obj = MedicationRecord.model_validate(record_tuple)
                #     med_id = record_obj.medication_id

                #     # If we haven't seen this medication_id yet, this is the most recent record
                #     # because of the ORDER BY clause.
                #     if med_id not in medications_data:
                #         medications_data[med_id] = {
                #             "current": record_obj.model_dump(), # Use .model_dump() for serialization
                #             "history": []
                #         }
                #     # If we have already seen this med_id, this record is an older one.
                #     else:
                #         medications_data[med_id]["history"].append(record_obj.model_dump())

                # for row in records:
                #     # Normalize to dict regardless of cursor type
                #     if isinstance(row, dict):
                #         record_dict = row
                #     else:
                #         record_dict = dict(zip(self.MED_DB_COLUMN_NAMES, row))

                #     # Ensure JSON columns are proper Python lists before validation
                #     for json_col in ("day_period", "day_of_week"):
                #         val = record_dict.get(json_col)
                #         if isinstance(val, str):
                #             try:
                #                 parsed = json.loads(val)
                #                 record_dict[json_col] = parsed if isinstance(parsed, list) else []
                #             except Exception:
                #                 record_dict[json_col] = []
                #         elif val is None:
                #             record_dict[json_col] = []

                #     # Validate/convert with Pydantic
                #     record_obj = MedicationRecord.model_validate(record_dict)
                #     med_id = record_obj.medication_id

                #     if med_id not in medications_data:
                #         medications_data[med_id] = {
                #             "current": record_obj.model_dump(),
                #             "history": []
                #         }
                #     else:
                #         medications_data[med_id]["history"].append(record_obj.model_dump())

            log = {"success": True, "error": None}
            return records, log

        except Exception as e:
            self.conn.rollback()
            logger.error(f"An error occurred: {e}")

            log = {"success": False, "error": str(e)}
            return {}, log


    def delete_medication_records(self, medication_id: str) -> Tuple[bool, dict]:
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

                query = "DELETE FROM medications_records WHERE medication_id = %s"
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
