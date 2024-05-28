# Path: ./sources/syntrillo/pseudonyms_management/temporary_lookup_codes_management.py

import uuid
import random
import MySQLdb
from syntrillo.databases_management.connection import create_connection
from syntrillo.databases_management.logs import add_log_entry

class TemporaryLookUpCodesManagement:
    """
    A class to manage temporary look-up codes in the Syntrillo database.

    Can create, retrieve, and manage entries in the user_look_up_temporary_codes table.

    Can create 2 types of entries:
    - 'iFrame' purpose used to identify iFrames and link them to a patient. Here the temporary code is a random UUID string.
    - 'Tenovi' purpose used to identify Tenovi devices and link them to a patient. Here the temporary code is a random string of 2 words, capitalized

    Can retrieve syntrillo internal key using the temporary code and its purpose.

    Can delete entries:
    - using the temporary code and its purpose.
    - more than 24 hours old entries.

    Add log entries, similar to the LookUpCodesManagement class.
    """

    def __init__(self, verbose=False):
        self.conn, self.tunnel = create_connection(verbose=verbose)
        self.cursor = self.conn.cursor()
        self.verbose = verbose

    def __del__(self):
        self.cursor.close()
        self.conn.close()
        if self.tunnel:
            self.tunnel.stop()
        if self.verbose:
            print("Database connection closed.")

    def generate_uuid_code(self):
        return str(uuid.uuid4())

    def generate_word_code(self):
        words = ["Apple", "Banana", "Cherry", "Date", "Fantastic",
                 "Grape", "Rainbow", "Kiwi", "Lemon", "Mango",
                 "Vacation", "Sunshine", "Snowball", "Watermelon",
                 "Fireworks", "Moon", "Star", "Sunny",
                 ]
        return random.choice(words).capitalize() + random.choice(words).capitalize()

    def create_temporary_code(self, syntrillo_internal_key, purpose):
        if purpose == 'iFrame':
            temp_code = self.generate_uuid_code()
        elif purpose == 'Tenovi':
            temp_code = self.generate_word_code()
        else:
            raise ValueError("Invalid purpose specified. Use 'iFrame' or 'Tenovi'.")

        query = """
            INSERT INTO user_look_up_temporary_codes (syntrillo_internal_key, temporary_pseudo_code, purpose, date)
            VALUES (UUID_TO_BIN(%s), %s, %s, NOW())
            ON DUPLICATE KEY UPDATE temporary_pseudo_code = VALUES(temporary_pseudo_code), date = NOW()
        """
        self.cursor.execute(query, (syntrillo_internal_key, temp_code, purpose))
        self.conn.commit()

        add_log_entry(self.cursor, "TemporaryLookUpCodesManagement", f"Created temporary code for purpose: {purpose}")

        return temp_code

    def retrieve_syntrillo_internal_key(self, temp_code, purpose):
        query = """
            SELECT BIN_TO_UUID(syntrillo_internal_key) FROM user_look_up_temporary_codes
            WHERE temporary_pseudo_code = %s AND purpose = %s
        """
        self.cursor.execute(query, (temp_code, purpose))
        result = self.cursor.fetchone()

        add_log_entry(self.cursor, "TemporaryLookUpCodesManagement", f"Retrieved syntrillo internal key for purpose: {purpose}")

        return result[0] if result else None

    def delete_entry(self, temp_code, purpose):
        query = """
            DELETE FROM user_look_up_temporary_codes
            WHERE temporary_pseudo_code = %s AND purpose = %s
        """
        self.cursor.execute(query, (temp_code, purpose))
        self.conn.commit()

        add_log_entry(self.cursor, "TemporaryLookUpCodesManagement", f"Deleted entry for temporary code: {temp_code} with purpose: {purpose}")

    def delete_old_entries(self):
        query = """
            DELETE FROM user_look_up_temporary_codes
            WHERE date < NOW() - INTERVAL 24 HOUR
        """
        self.cursor.execute(query)
        self.conn.commit()

        add_log_entry(self.cursor, "TemporaryLookUpCodesManagement", "Deleted entries older than 24 hours")

# Example usage:
if __name__ == "__main__":
    manager = TemporaryLookUpCodesManagement(verbose=True)

    # Example syntrillo_internal_key, replace with a real key if needed
    syntrillo_internal_key = str(uuid.uuid4())

    # Create a temporary code for 'iFrame' purpose
    temp_code_iframe = manager.create_temporary_code(syntrillo_internal_key, 'iFrame')
    print(f"Temporary Code for iFrame: {temp_code_iframe}")

    # Create a temporary code for 'Tenovi' purpose
    temp_code_tenovi = manager.create_temporary_code(syntrillo_internal_key, 'Tenovi')
    print(f"Temporary Code for Tenovi: {temp_code_tenovi}")

    # Retrieve syntrillo internal key using the temporary code and purpose
    retrieved_key_iframe = manager.retrieve_syntrillo_internal_key(temp_code_iframe, 'iFrame')
    print(f"Retrieved Syntrillo Internal Key for iFrame: {retrieved_key_iframe}")

    retrieved_key_tenovi = manager.retrieve_syntrillo_internal_key(temp_code_tenovi, 'Tenovi')
    print(f"Retrieved Syntrillo Internal Key for Tenovi: {retrieved_key_tenovi}")

    # Delete an entry using the temporary code and purpose
    manager.delete_entry(temp_code_iframe, 'iFrame')
    print(f"Deleted Temporary Code for iFrame: {temp_code_iframe}")

    # Delete old entries (older than 24 hours)
    manager.delete_old_entries()
    print("Deleted entries older than 24 hours.")
