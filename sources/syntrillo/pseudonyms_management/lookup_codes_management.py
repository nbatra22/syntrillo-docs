# Path: ./sources/syntrillo/pseudonyms_management/lookup_codes_management.py

import uuid
import pymysql
from syntrillo.databases_management.connection import DatabaseConnection
from syntrillo.databases_management.logs import add_log_entry

from aws_lambda_powertools import Logger
logger = Logger(service="PROVIDER_TAB")

class LookUpCodesManagement:
    """
    A class to manage look-up codes in the Syntrillo Pseudonym Management database.

    This class provides methods to create, retrieve, and manage entries in the
    user_look_up_codes table. Each entry links a healthie user ID to a syntrillo
    internal key and a pseudo code for accessing PHI (Protected Health Information).

    Attributes:
    -----------
    conn : pymysql.connections.Connection
        The database connection object.
    cursor : MySQLdb.cursors.Cursor
        The cursor object for executing SQL queries.
    tunnel : sshtunnel.SSHTunnelForwarder
        The SSH tunnel object for secure database connections.
    verbose : bool
        Flag to enable verbose logging and connection details.

    Methods:
    --------
    create_entry(healthie_user_id):
        Creates a new entry for a healthie user ID in the user_look_up_codes table.

    retrieve_entry_by_healthie_user_id(healthie_user_id):
        Retrieves an entry using the healthie user ID.

    retrieve_entry_by_internal_key(internal_key):
        Retrieves an entry using the syntrillo internal key.

    retrieve_entry_by_pseudo_code(pseudo_code):
        Retrieves an entry using the pseudo code for accessing PHI.

    close_connection():
        Closes the database connection and stops the SSH tunnel if applicable.
    """

    def __init__(self, verbose=False):
        """
        Initialize the LookUpCodesManagement class.

        :param verbose: If True, enables verbose mode for detailed logging and connection info.
        """

        self.db_conn = DatabaseConnection(DatabaseConnection.PSEUDONYM_DB)
        self.conn, self.tunnel = self.db_conn.create_connection(verbose=verbose)
        self.cursor = self.conn.cursor()
        self.verbose = verbose

        logger.debug(f"=====% INIT LOOKUP CODES MANAGEMENT")

    def __del__(self):
        try:
            self.cursor.close()
            if self.conn:
                self.conn.close()
                if self.tunnel:
                    self.tunnel.stop()
                if self.verbose:
                    print("Database connection closed.")
        except pymysql.OperationalError as e:
            print(f"OperationalError during connection close: {e}")
        except Exception as e:
            print(f"Unexpected error during connection close: {e}")


    def create_entry(self, healthie_user_id):
        """
        Create a new entry in the user_look_up_codes table for the specified healthie_user_id.

        :param healthie_user_id: The ID of the healthie user.
        :return: A dictionary with syntrillo_internal_key and pseudo_code_for_tenovi_phi_access, or None if creation failed.
        """

        create_entry_query = """
        INSERT INTO user_look_up_codes (healthie_user_id, syntrillo_internal_key, pseudo_code_for_tenovi_phi_access, date)
        VALUES (%s, %s, %s, NOW());
        """

        try:
            syntrillo_internal_key = uuid.uuid4().bytes
            pseudo_code_for_tenovi_phi_access = uuid.uuid4().bytes

            self.cursor.execute(create_entry_query, (healthie_user_id, syntrillo_internal_key, pseudo_code_for_tenovi_phi_access))
            self.conn.commit()

            select_query = """
            SELECT
                BIN_TO_UUID(syntrillo_internal_key) as syntrillo_internal_key,
                BIN_TO_UUID(pseudo_code_for_tenovi_phi_access) as pseudo_code_for_tenovi_phi_access
            FROM user_look_up_codes
            WHERE healthie_user_id = %s;
            """
            self.cursor.execute(select_query, (healthie_user_id,))
            entry = self.cursor.fetchone()

            if entry:
                result = {
                    'syntrillo_internal_key': str(uuid.UUID(entry[0])),
                    'pseudo_code_for_tenovi_phi_access': str(uuid.UUID(entry[1]))
                }
                add_log_entry(event='CREATE_ENTRY', json_data=str(result), comment=f"Entry created for healthie_user_id {healthie_user_id}")
                return result
            else:
                add_log_entry(event='CREATE_ENTRY_FAILED', json_data=str(healthie_user_id), comment="Failed to retrieve the newly created entry.")
                return None
        except pymysql.MySQLError as e:
            self.conn.rollback()
            add_log_entry(event='CREATE_ENTRY_ERROR', json_data=str(healthie_user_id), comment=str(e))
            return None

    def retrieve_entry_by_healthie_user_id(self, healthie_user_id):
        """
        Retrieve an entry from the user_look_up_codes table using the healthie_user_id.

        :param healthie_user_id: The ID of the healthie user.
        :return: A dictionary with syntrillo_internal_key and pseudo_code_for_tenovi_phi_access, or None if no entry is found.
        """

        select_query = """
        SELECT
            BIN_TO_UUID(syntrillo_internal_key) as syntrillo_internal_key,
            BIN_TO_UUID(pseudo_code_for_tenovi_phi_access) as pseudo_code_for_tenovi_phi_access
        FROM user_look_up_codes
        WHERE healthie_user_id = %s;
        """
        self.cursor.execute(select_query, (healthie_user_id,))
        entry = self.cursor.fetchone()
        if entry:
            result = {
                'syntrillo_internal_key': str(uuid.UUID(entry[0])),
                'pseudo_code_for_tenovi_phi_access': str(uuid.UUID(entry[1]))
            }
            add_log_entry(event='RETRIEVE_ENTRY_BY_healthie_USER_ID', json_data=str(result), comment=f"Entry retrieved for healthie_user_id {healthie_user_id}")
            return result
        else:
            add_log_entry(event='RETRIEVE_ENTRY_BY_healthie_USER_ID_FAILED', json_data=str(healthie_user_id), comment="No entry found.")
            return None

    def retrieve_entry_by_internal_key(self, internal_key):
        """
        Retrieve an entry from the user_look_up_codes table using the syntrillo_internal_key.

        :param internal_key: The syntrillo internal key (UUID).
        :return: A dictionary with healthie_user_id and pseudo_code_for_tenovi_phi_access, or None if no entry is found.
        """

        select_query = """
        SELECT
            healthie_user_id,
            BIN_TO_UUID(pseudo_code_for_tenovi_phi_access) as pseudo_code_for_tenovi_phi_access
        FROM user_look_up_codes
        WHERE syntrillo_internal_key = UUID_TO_BIN(%s);
        """
        self.cursor.execute(select_query, (internal_key,))
        entry = self.cursor.fetchone()
        if entry:
            result = {
                'healthie_user_id': entry[0],
                'pseudo_code_for_tenovi_phi_access': str(uuid.UUID(entry[1]))
            }
            add_log_entry(event='RETRIEVE_ENTRY_BY_INTERNAL_KEY', json_data=str(result), comment=f"Entry retrieved for syntrillo_internal_key {internal_key}")
            return result
        else:
            add_log_entry(event='RETRIEVE_ENTRY_BY_INTERNAL_KEY_FAILED', json_data=str(internal_key), comment="No entry found.")
            return None

    def retrieve_entry_by_pseudo_code(self, pseudo_code):
        """
        Retrieve an entry from the user_look_up_codes table using the pseudo_code_for_tenovi_phi_access.

        :param pseudo_code: The pseudo code (UUID).
        :return: A dictionary with healthie_user_id and syntrillo_internal_key, or None if no entry is found.
        """

        select_query = """
        SELECT
            healthie_user_id,
            BIN_TO_UUID(syntrillo_internal_key) as syntrillo_internal_key
        FROM user_look_up_codes
        WHERE pseudo_code_for_tenovi_phi_access = UUID_TO_BIN(%s);
        """
        self.cursor.execute(select_query, (pseudo_code,))
        entry = self.cursor.fetchone()
        if entry:
            result = {
                'healthie_user_id': entry[0],
                'syntrillo_internal_key': str(uuid.UUID(entry[1]))
            }
            add_log_entry(event='RETRIEVE_ENTRY_BY_PSEUDO_CODE', json_data=str(result), comment=f"Entry retrieved for pseudo_code_for_tenovi_phi_access {pseudo_code}")
            return result
        else:
            add_log_entry(event='RETRIEVE_ENTRY_BY_PSEUDO_CODE_FAILED', json_data=str(pseudo_code), comment="No entry found.")
            return None

    def close_connection(self):
        """
        Close the database connection and stop the SSH tunnel if applicable.
        """
        if self.conn:
            self.cursor.close()
            self.conn.close()
            self.tunnel.stop() if self.tunnel else None
            print("Database connection closed.")


if __name__ == "__main__":
    import random
    from datetime import datetime

    # Generate a random number and a date stamp
    random_number = random.randint(1000, 9999)
    date_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    healthie_user_id = f"test_{random_number}_{date_stamp}"

    # Initialize LookUpCodesManagement instance
    lookup_manager = LookUpCodesManagement(verbose=True)

    # Test create_entry method
    print(f"Creating entry for healthie_user_id: {healthie_user_id}")
    create_result = lookup_manager.create_entry(healthie_user_id)
    print(f"Create entry result: {create_result}")

    # Test retrieve_entry_by_healthie_user_id method
    if create_result:
        print(f"Retrieving entry for healthie_user_id: {healthie_user_id}")
        retrieve_result = lookup_manager.retrieve_entry_by_healthie_user_id(healthie_user_id)
        print(f"Retrieve entry result: {retrieve_result}")

    # Close the database connection
    lookup_manager.close_connection()

