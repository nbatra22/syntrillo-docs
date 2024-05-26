# Path: ./sources/syntrillo/databases_management/set-up_user_loop-up_tables.py

import MySQLdb
from syntrillo.databases_management.connection import create_connection

class UserLookupTablesManager:
    """
    A class to manage the creation and deletion of user lookup tables in a MySQL database.
    The tables store pseudonymized user data for regulatory compliance.
    """

    def __init__(self):
        """
        Initialize the UserLookupTablesManager by creating a database connection.
        """

        if __name__ != "__main__":
            raise RuntimeError("UserLookupTablesManager class can only be instantiated interactively.")

        self.conn, self.tunnel = create_connection(verbose=True)
        if not self.conn:
            raise ConnectionError("Failed to connect to the database.")
        self.cursor = self.conn.cursor()

    def create_user_lookup_tables(self):
        """
        Create the user lookup tables if they do not exist.

        Pseudonyms, codes, ids, keys are specific to each party to enhance segregation and adaptability. This database is the only place where the pseudonymized data is stored together to allow re-identifcation of subjects when necessary, as described in the hipaa safe harbor regulations.

        Table and field names are as clear as possible and carry their respective function.

        Tables:
        - user_look_up_codes: Stores the relationship between internal keys and pseudonymized codes.
        - user_look_up_temporary_codes: Stores temporary pseudonymized codes for user identification.

        syntrillo_internal_key is a fixed-length key for internal identification, and is Syntrillo specific

        Per protocol : 'We maintain compliance by programmatically creating and assigning internal identifiers linking records across platforms and making these identifiers difficult or impossible to view or modify by staff or patients.  Within the Tenovi platform, we will assign each participant a unique  "Pseudo Look-Up Code" . This platform-specific pseudonym, ensures that PHI is queried and retrieved securely while maintaining the privacy of participants.  Within the Healthie platform, we will use user look-up codes to re-identify participants. Look-up codes and pseudonyms will be generated programmatically via API calls triggered automatically by specific events (e.g. new patient added, Tenovi account created, etc) and will not be readily accessible to Syntrillo staff or patients.'

        Per protocol : 'To safeguard the data, within the Syntrillo platform we will generate internal unique codes linked to third-party pseudonyms and third-party codes via a secure look-up table hosted on a dedicated database. We will implement strict access controls, allowing only authorized personnel to access the look-up table containing the re-identification code. Robust encryption methods will be used for data at rest and in transit.'


        """
        create_user_lookup_codes_table = """
        CREATE TABLE IF NOT EXISTS user_look_up_codes (
            id INT AUTO_INCREMENT PRIMARY KEY,                      # Auto-increment ID for unique identification

            # Internal key, fixed length for consistency
            syntrillo_internal_key CHAR(16) UNIQUE,

            # Pseudonymized code for access control
            pseudo_code_for_tenovi_phi_access CHAR(16) UNIQUE,

            # External user ID, fixed length for consistency
            healthy_user_id CHAR(16) UNIQUE,

            # Date of creation for audit purposes
            date DATETIME,

            # Enforce unique relationships
            UNIQUE(syntrillo_internal_key, healthy_user_id),
            UNIQUE(syntrillo_internal_key, pseudo_code_for_tenovi_phi_access)
        );
        """
        create_user_lookup_temporary_codes_table = """
        CREATE TABLE IF NOT EXISTS user_look_up_temporary_codes (
            id INT AUTO_INCREMENT PRIMARY KEY,                  # Auto-increment ID for unique identification

            # Internal key, fixed length for consistency
            syntrillo_internal_key CHAR(16),

            # Temporary pseudonymized code for temporary access (many to one relationship with syntrillo_internal_key)
            temporary_pseudo_code VARCHAR(255),

            # Date of creation for scheduled deletion
            date DATETIME,

            INDEX (syntrillo_internal_key),
            INDEX (temporary_pseudo_code)
        );
        """
        try:
            self.cursor.execute(create_user_lookup_codes_table)
            self.cursor.execute(create_user_lookup_temporary_codes_table)
            self.conn.commit()
            print("User lookup tables created successfully.")
        except MySQLdb.Error as e:
            self.conn.rollback()
            print(f"Error creating tables: {e}")

    def drop_user_lookup_tables(self):
        """
        Drop the user lookup tables interactively with a warning.

        Tables:
        - user_look_up_codes: Stores the relationship between internal keys and pseudonymized codes.
        - user_look_up_temporary_codes: Stores temporary pseudonymized codes for user identification.

        """
        tables = ["user_look_up_codes", "user_look_up_temporary_codes"]
        for table in tables:
            confirm = input(f"Are you sure you want to drop the table '{table}'? This action cannot be undone (yes/no): ")
            if confirm.lower() == "yes":
                try:
                    self.cursor.execute(f"DROP TABLE IF EXISTS {table};")
                    self.conn.commit()
                    print(f"Table '{table}' dropped successfully.")
                except MySQLdb.Error as e:
                    self.conn.rollback()
                    print(f"Error dropping table '{table}': {e}")
            else:
                print(f"Skipping drop for table '{table}'.")

    def close_connection(self):
        """
        Close the database connection and cursor.
        """
        if self.conn:
            self.cursor.close()
            self.conn.close()
            self.tunnel.stop() if self.tunnel else None
            print("Database connection closed.")

if __name__ == '__main__':
    manager = UserLookupTablesManager()

    while True:
        action = input("Choose an action: 'create' to create tables, 'drop' to drop tables, 'exit' to quit: ").lower()
        if action == "create":
            manager.create_user_lookup_tables()
        elif action == "drop":
            manager.drop_user_lookup_tables()
        elif action == "exit":
            manager.close_connection()
            break
        else:
            print("Invalid action. Please choose 'create', 'drop', or 'exit'.")

