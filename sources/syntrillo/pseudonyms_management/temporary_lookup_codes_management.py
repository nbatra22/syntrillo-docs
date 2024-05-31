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

    PURPOSE_TENOVI_PAIRING = 'TenoviPairing'
    PURPOSE_HEALTHIE_IFRAME = 'Healthie-iFrame'

    def __init__(self, verbose=False):
        """
        Initializes the TemporaryLookUpCodesManagement class, setting up the database connection and cursor.
        """
        self.conn, self.tunnel = create_connection(verbose=verbose)
        self.cursor = self.conn.cursor()
        self.verbose = verbose

    def __del__(self):
        """
        Destructor for the TemporaryLookUpCodesManagement class, closing the database connection and cursor.
        """
        self.cursor.close()
        self.conn.close()
        if self.tunnel:
            self.tunnel.stop()
        if self.verbose:
            print("Database connection closed.")

    def generate_uuid_code(self):
        """
        Generates a random UUID code.

        Returns:
            str: A random UUID string.
        """
        return str(uuid.uuid4())

    def generate_word_code(self):
        """
        Generates a random code consisting of two capitalized words.

        Returns:
            str: A random string of two capitalized words concatenated together.
        """
        words = ["Apple", "Banana", "Cherry", "Date", "Fantastic",
                 "Grape", "Rainbow", "Kiwi", "Lemon", "Mango",
                 "Vacation", "Sunshine", "Snowball", "Watermelon",
                 "Fireworks", "Moon", "Star", "Sunny",
                 ]
        return random.choice(words).capitalize() + random.choice(words).capitalize()

    def remove_all_temporary_codes_for_syntrillo_internal_key(self, syntrillo_internal_key: str, purpose: str):
        """

        """
        query = """
            DELETE FROM user_look_up_temporary_codes
            WHERE syntrillo_internal_key = UUID_TO_BIN(%s) AND purpose = %s
        """
        self.cursor.execute(query, (syntrillo_internal_key, purpose))
        self.conn.commit()

        add_log_entry(self.cursor, "TemporaryLookUpCodesManagement",
                      f"Deleted all entries for syntrillo internal key: {syntrillo_internal_key} with purpose: {purpose}"
                      )


    def create_temporary_pseudo_code(self, syntrillo_internal_key: str, purpose: str):
        """
        Creates a temporary pseudo code for a given syntrillo_internal_key and purpose.

        Args:
            syntrillo_internal_key (str): The internal key for the Syntrillo system.
            purpose (str): The purpose of the temporary code (PURPOSE_HEALTHIE_IFRAME or PURPOSE_TENOVI_PAIRING).

        Returns:
            str: The generated temporary pseudo code.

        Raises:
            ValueError: If the purpose is not 'iFrame' or 'Tenovi'.
        """
        if purpose == self.PURPOSE_HEALTHIE_IFRAME:
            temp_code = self.generate_uuid_code()
        elif purpose == self.PURPOSE_TENOVI_PAIRING:
            temp_code = self.generate_word_code()
        else:
            raise ValueError("Invalid purpose specified.")

        try:
            # Lock the table
            self.cursor.execute("LOCK TABLES user_look_up_temporary_codes WRITE")

            # remove all pseudo codes for this syntrillo_internal_key and Tenovi purpose
            # only one Tenovi temporary pseudo code should be active at a time
            if purpose == self.PURPOSE_TENOVI_PAIRING:
                self.remove_all_temporary_codes_for_syntrillo_internal_key(syntrillo_internal_key, purpose)

            while True:
                # Check if the temporary code already exists
                query_check = """
                    SELECT COUNT(*) FROM user_look_up_temporary_codes
                    WHERE temporary_pseudo_code = %s
                """
                self.cursor.execute(query_check, (temp_code, ))
                count = self.cursor.fetchone()[0]

                # break if it doesn't exist
                if count == 0:
                    break

                # Regenerate the code if it already exists and loop again
                if purpose == self.PURPOSE_HEALTHIE_IFRAME:
                    temp_code = self.generate_uuid_code()
                elif purpose == self.PURPOSE_TENOVI_PAIRING:
                    temp_code = self.generate_word_code()

            # Insert the new temporary code
            query_insert = """
                INSERT INTO user_look_up_temporary_codes (syntrillo_internal_key, temporary_pseudo_code, purpose, date)
                VALUES (UUID_TO_BIN(%s), %s, %s, NOW())
            """
            self.cursor.execute(query_insert, (syntrillo_internal_key, temp_code, purpose))
            self.conn.commit()

            add_log_entry(self.cursor, "TemporaryLookUpCodesManagement", f"Created temporary code for purpose: {purpose}")

        finally:
            # Always release the lock
            self.cursor.execute("UNLOCK TABLES")

        return temp_code

    def retrieve_tenovi_pairing_temporary_pseudo_code(self, syntrillo_internal_key: str):
        """
        Retrieves the Tenovi temporary pseudo code for a given syntrillo_internal_key.

        Args:
            syntrillo_internal_key (str): The internal key for the Syntrillo system.

        Returns:
            str: The Tenovi temporary pseudo code if found, None otherwise.
        """
        query = """
            SELECT temporary_pseudo_code FROM user_look_up_temporary_codes
            WHERE syntrillo_internal_key = UUID_TO_BIN(%s) AND purpose = %s
        """
        self.cursor.execute(query, (syntrillo_internal_key, self.PURPOSE_TENOVI_PAIRING))
        result = self.cursor.fetchone()

        add_log_entry(self.cursor, "TemporaryLookUpCodesManagement",
                      f"Retrieved Tenovi temporary pseudo code for syntrillo_internal_key: {syntrillo_internal_key}")

        return result[0] if result else None


    def retrieve_syntrillo_internal_key(self, temp_code, purpose):
        """
        Retrieves the syntrillo internal key using the temporary code and its purpose.

        Args:
            temp_code (str): The temporary pseudo code.
            purpose (str): The purpose of the temporary code.

        Returns:
            str: The syntrillo internal key if found, None otherwise.
        """
        query = """
            SELECT BIN_TO_UUID(syntrillo_internal_key) FROM user_look_up_temporary_codes
            WHERE temporary_pseudo_code = %s AND purpose = %s
        """
        self.cursor.execute(query, (temp_code, purpose))
        result = self.cursor.fetchone()

        add_log_entry(self.cursor, "TemporaryLookUpCodesManagement", f"Retrieved syntrillo internal key for purpose: {purpose}")

        return result[0] if result else None

    def delete_entry(self, temp_code, purpose):
        """
        Deletes an entry using the temporary code and its purpose.

        Args:
            temp_code (str): The temporary pseudo code.
            purpose (str): The purpose of the temporary code.
        """
        query = """
            DELETE FROM user_look_up_temporary_codes
            WHERE temporary_pseudo_code = %s AND purpose = %s
        """
        self.cursor.execute(query, (temp_code, purpose))
        self.conn.commit()

        add_log_entry(self.cursor, "TemporaryLookUpCodesManagement", f"Deleted entry for temporary code: {temp_code} with purpose: {purpose}")

    def delete_old_entries(self):
        """
        Deletes entries that are more than 24 hours old.
        """
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
    temp_code_iframe = manager.create_temporary_pseudo_code(syntrillo_internal_key, TemporaryLookUpCodesManagement.PURPOSE_HEALTHIE_IFRAME)
    print(f"Temporary Code for iFrame: {temp_code_iframe}")

    # Create a temporary code for 'Tenovi' purpose
    temp_code_tenovi = manager.create_temporary_pseudo_code(syntrillo_internal_key, TemporaryLookUpCodesManagement.PURPOSE_TENOVI_PAIRING)
    print(f"Temporary Code for Tenovi: {temp_code_tenovi}")

    # Retrieve syntrillo internal key using the temporary code and purpose
    retrieved_key_iframe = manager.retrieve_syntrillo_internal_key(temp_code_iframe, TemporaryLookUpCodesManagement.PURPOSE_HEALTHIE_IFRAME)
    print(f"Retrieved Syntrillo Internal Key for iFrame: {retrieved_key_iframe}")

    retrieved_key_tenovi = manager.retrieve_syntrillo_internal_key(temp_code_tenovi, TemporaryLookUpCodesManagement.PURPOSE_TENOVI_PAIRING)
    print(f"Retrieved Syntrillo Internal Key for Tenovi: {retrieved_key_tenovi}")

    # Delete an entry using the temporary code and purpose
    manager.delete_entry(temp_code_iframe, TemporaryLookUpCodesManagement.PURPOSE_HEALTHIE_IFRAME)
    print(f"Deleted Temporary Code for iFrame: {temp_code_iframe}")

    # Delete old entries (older than 24 hours)
    manager.delete_old_entries()
    print("Deleted entries older than 24 hours.")
