# Path: ./sources/syntrillo/pseudonyms_management/lookup_codes_management.py

import uuid
import MySQLdb
from syntrillo.databases_management.connection import create_connection
from syntrillo.databases_management.logs import add_log_entry

class LookUpCodesManagement:
    def __init__(self, verbose=False):
        self.conn, self.tunnel = create_connection(verbose=verbose)
        self.cursor = self.conn.cursor()
        self.verbose = verbose

    def create_entry(self, healthy_user_id):
        create_entry_query = """
        INSERT INTO user_look_up_codes (healthy_user_id, date)
        VALUES (%s, NOW());
        """
        try:
            self.cursor.execute(create_entry_query, (healthy_user_id,))
            self.conn.commit()

            select_query = """
            SELECT
                BIN_TO_UUID(syntrillo_internal_key) as syntrillo_internal_key,
                BIN_TO_UUID(pseudo_code_for_tenovi_phi_access) as pseudo_code_for_tenovi_phi_access
            FROM user_look_up_codes
            WHERE healthy_user_id = %s;
            """
            self.cursor.execute(select_query, (healthy_user_id,))
            entry = self.cursor.fetchone()

            if entry:
                result = {
                    'syntrillo_internal_key': str(uuid.UUID(entry[0])),
                    'pseudo_code_for_tenovi_phi_access': str(uuid.UUID(entry[1]))
                }
                add_log_entry(event='CREATE_ENTRY', json_data=str(result), comment=f"Entry created for healthy_user_id {healthy_user_id}")
                return result
            else:
                add_log_entry(event='CREATE_ENTRY_FAILED', json_data=str(healthy_user_id), comment="Failed to retrieve the newly created entry.")
                return None
        except MySQLdb.Error as e:
            self.conn.rollback()
            add_log_entry(event='CREATE_ENTRY_ERROR', json_data=str(healthy_user_id), comment=str(e))
            return None

    def retrieve_entry_by_healthy_user_id(self, healthy_user_id):
        select_query = """
        SELECT
            BIN_TO_UUID(syntrillo_internal_key) as syntrillo_internal_key,
            BIN_TO_UUID(pseudo_code_for_tenovi_phi_access) as pseudo_code_for_tenovi_phi_access
        FROM user_look_up_codes
        WHERE healthy_user_id = %s;
        """
        self.cursor.execute(select_query, (healthy_user_id,))
        entry = self.cursor.fetchone()
        if entry:
            result = {
                'syntrillo_internal_key': str(uuid.UUID(entry[0])),
                'pseudo_code_for_tenovi_phi_access': str(uuid.UUID(entry[1]))
            }
            add_log_entry(event='RETRIEVE_ENTRY_BY_HEALTHY_USER_ID', json_data=str(result), comment=f"Entry retrieved for healthy_user_id {healthy_user_id}")
            return result
        else:
            add_log_entry(event='RETRIEVE_ENTRY_BY_HEALTHY_USER_ID_FAILED', json_data=str(healthy_user_id), comment="No entry found.")
            return None

    def retrieve_entry_by_internal_key(self, internal_key):
        select_query = """
        SELECT
            healthy_user_id,
            BIN_TO_UUID(pseudo_code_for_tenovi_phi_access) as pseudo_code_for_tenovi_phi_access
        FROM user_look_up_codes
        WHERE syntrillo_internal_key = UUID_TO_BIN(%s);
        """
        self.cursor.execute(select_query, (internal_key,))
        entry = self.cursor.fetchone()
        if entry:
            result = {
                'healthy_user_id': entry[0],
                'pseudo_code_for_tenovi_phi_access': str(uuid.UUID(entry[1]))
            }
            add_log_entry(event='RETRIEVE_ENTRY_BY_INTERNAL_KEY', json_data=str(result), comment=f"Entry retrieved for syntrillo_internal_key {internal_key}")
            return result
        else:
            add_log_entry(event='RETRIEVE_ENTRY_BY_INTERNAL_KEY_FAILED', json_data=str(internal_key), comment="No entry found.")
            return None

    def retrieve_entry_by_pseudo_code(self, pseudo_code):
        select_query = """
        SELECT
            healthy_user_id,
            BIN_TO_UUID(syntrillo_internal_key) as syntrillo_internal_key
        FROM user_look_up_codes
        WHERE pseudo_code_for_tenovi_phi_access = UUID_TO_BIN(%s);
        """
        self.cursor.execute(select_query, (pseudo_code,))
        entry = self.cursor.fetchone()
        if entry:
            result = {
                'healthy_user_id': entry[0],
                'syntrillo_internal_key': str(uuid.UUID(entry[1]))
            }
            add_log_entry(event='RETRIEVE_ENTRY_BY_PSEUDO_CODE', json_data=str(result), comment=f"Entry retrieved for pseudo_code_for_tenovi_phi_access {pseudo_code}")
            return result
        else:
            add_log_entry(event='RETRIEVE_ENTRY_BY_PSEUDO_CODE_FAILED', json_data=str(pseudo_code), comment="No entry found.")
            return None

    def close_connection(self):
        if self.conn:
            self.cursor.close()
            self.conn.close()
            self.tunnel.stop() if self.tunnel else None
            print("Database connection closed.")
