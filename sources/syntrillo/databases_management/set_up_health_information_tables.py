# Path: ./sources/syntrillo/databases_management/set_up_health_information_tables.py
import pymysql
from syntrillo.databases_management.connection import DatabaseConnection

class HealthInformationTablesManager:
    """
    A class to manage the creation and deletion of health information tables in a MySQL database.

    It can only be instantiated interactively.

    Warning : This class can drop tables. Use with caution.

    """

    # Health Information Tables as class variables
    MISC_HEALTH_DATA_TABLE = "misc_health_data"
    TENOVI_RAW_MEASUREMENTS_TABLE = "tenovi_raw_measurements"
    HEALTHIE_QUESTIONNAIRES_TABLE = "healthie_questionnaires"

    # TODO : new tables to implement
    PREFERENCES_PATIENT_TABLE = "preferences_patient"
    PREFERENCES_STAFF_TABLE = "preferences_staff"
    AI_CHATBOT_SESSIONS_TABLE = "ai_chatbot_sessions"
    AI_KNOWLEDGE_BASE_TABLE = "ai_knowledge_base"

    # Dictionary mapping table names to their SQL creation queries
    TABLE_CREATION_QUERIES = {
        MISC_HEALTH_DATA_TABLE: f"""
        CREATE TABLE IF NOT EXISTS {MISC_HEALTH_DATA_TABLE} (
            id                          INT AUTO_INCREMENT PRIMARY KEY,
            syntrillo_internal_key      BINARY(16) NOT NULL,
            data_type                   VARCHAR(255) NOT NULL,
            data_json                   JSON NOT NULL,
            date                        DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX (syntrillo_internal_key),
            INDEX (data_type)
        );
        """,
        TENOVI_RAW_MEASUREMENTS_TABLE: f"""
        CREATE TABLE IF NOT EXISTS {TENOVI_RAW_MEASUREMENTS_TABLE} (
            id                          INT AUTO_INCREMENT PRIMARY KEY,
            syntrillo_internal_key      BINARY(16) NOT NULL,
            device_name                 VARCHAR(255) NOT NULL,
            -- metric_name : json data copied here to speed-up access
            metric_name                 VARCHAR(255) NOT NULL,
            value_1                     VARCHAR(255) DEFAULT NULL,
            value_2                     VARCHAR(255) DEFAULT NULL,
            -- timestamp with isoformat: patient local time + timezone_offset from the device
            timestamp_local             VARCHAR(255) NOT NULL,
            data_json                   JSON NOT NULL,
            date                        DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX (syntrillo_internal_key),
            INDEX (device_name)
        );
        """,
        HEALTHIE_QUESTIONNAIRES_TABLE: f"""
        CREATE TABLE IF NOT EXISTS {HEALTHIE_QUESTIONNAIRES_TABLE} (
            id                          INT AUTO_INCREMENT PRIMARY KEY,
            platform                    VARCHAR(255) DEFAULT NULL, -- prod or staging
            name                        VARCHAR(255) NOT NULL,
            version                     VARCHAR(255) NOT NULL,
            structure_json              JSON NOT NULL,
            -- mediumblob : up to 16MB
            excel_file                  MEDIUMBLOB DEFAULT NULL,
            date                        DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """,
    }

    # TODO : use INDEX (platform, name, version) instead of UNIQUE (platform, name, version) ?

    TODO_TABLE_CREATION_QUERIES = {
        PREFERENCES_PATIENT_TABLE: f"""
        CREATE TABLE IF NOT EXISTS {PREFERENCES_PATIENT_TABLE} (
            id                          INT AUTO_INCREMENT PRIMARY KEY,
            syntrillo_internal_key      BINARY(16) NOT NULL,
            platform                    VARCHAR(255) DEFAULT NULL,
            item                        VARCHAR(255) DEFAULT NULL,
            settings                    VARCHAR(255) DEFAULT NULL,
            items_json                  JSON DEFAULT NULL,
            settings_json               JSON DEFAULT NULL,
            date                        DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX (syntrillo_internal_key)
        );
        """,
        PREFERENCES_STAFF_TABLE: f"""
        CREATE TABLE IF NOT EXISTS {PREFERENCES_STAFF_TABLE} (
            id                          INT AUTO_INCREMENT PRIMARY KEY,
            staff_id_json               JSON NOT NULL,
            platform                    VARCHAR(255) DEFAULT NULL,
            item                        VARCHAR(255) DEFAULT NULL,
            settings                    VARCHAR(255) DEFAULT NULL,
            items_json                  JSON DEFAULT NULL,
            settings_json               JSON DEFAULT NULL,
            date                        DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """,
        AI_CHATBOT_SESSIONS_TABLE: f"""
        CREATE TABLE IF NOT EXISTS {AI_CHATBOT_SESSIONS_TABLE} (
            id                          INT AUTO_INCREMENT PRIMARY KEY,
            chatbot_name                VARCHAR(255) DEFAULT NULL,
            healthie_conversation_id    VARCHAR(255) DEFAULT NULL,
            data_json                   JSON DEFAULT NULL,
            messages_json               JSON DEFAULT NULL,
            paths_json                  JSON DEFAULT NULL,
            date                        DATETIME DEFAULT CURRENT_TIMESTAMP,
        );
        """,
        AI_KNOWLEDGE_BASE_TABLE: f"""
        CREATE TABLE IF NOT EXISTS {AI_KNOWLEDGE_BASE_TABLE} (
            id                          INT AUTO_INCREMENT PRIMARY KEY,
        );
        """,
    }

    def __init__(self):
        """
        Initialize the HealthInformationTablesManager by creating a database connection.
        """

        if __name__ != "__main__":
            raise RuntimeError("HealthInformationTablesManager class can only be instantiated interactively.")

        db_conn = DatabaseConnection(DatabaseConnection.HEALTH_INFO_DB)
        self.conn, self.tunnel = db_conn.create_connection(verbose=True)
        if not self.conn:
            raise ConnectionError("Failed to connect to the database.")
        self.cursor = self.conn.cursor()


    def create_health_data_tables(self):
        """
        Create the PHI tables.
        Checks if each table exists before attempting to create it.
        Commits after each successful table creation.
        """
        try:
            for table_name, create_sql in self.TABLE_CREATION_QUERIES.items():
                try:
                    # Check if the table already exists
                    self.cursor.execute(f"SHOW TABLES LIKE '{table_name}';")
                    result = self.cursor.fetchone()

                    if result:
                        print(f"Table '{table_name}' already exists.")
                    else:
                        # Table doesn't exist, so create it
                        self.cursor.execute(create_sql)
                        self.conn.commit()  # Commit after table creation
                        print(f"Table '{table_name}' created successfully.")
                except pymysql.MySQLError as e:
                    self.conn.rollback()  # Rollback only for the current table
                    print(f"Error creating table '{table_name}': {e}")
        except pymysql.MySQLError as e:
            print(f"General error during table creation: {e}")


    def drop_user_lookup_tables(self):
        """
        Drop the user PHI tables interactively with a warning.
        """
        for table in self.TABLE_CREATION_QUERIES.keys():
            confirm = input(f"Are you sure you want to drop the table '{table}'? This action cannot be undone (yes/no): ")
            if confirm.lower() == "yes":
                try:
                    self.cursor.execute(f"DROP TABLE IF EXISTS {table};")
                    self.conn.commit()
                    print(f"Table '{table}' dropped successfully.")
                except pymysql.MySQLError as e:
                    self.conn.rollback()
                    print(f"Error dropping table '{table}': {e}")
            else:
                print(f"Skipping drop for table '{table}'.")

    def report_tables_status(self):
        """
        Report if the tables exist and their number of records.
        """
        for table in self.TABLE_CREATION_QUERIES.keys():
            try:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = self.cursor.fetchone()[0]
                print(f"Table '{table}' exists with {count} records.")
            except pymysql.MySQLError as e:
                print(f"Table '{table}' does not exist or cannot be accessed: {e}")


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
    manager = HealthInformationTablesManager()

    print("\n")
    manager.report_tables_status()

    while True:
        action = input("\nChoose an action: 'create' to create tables, 'drop' to drop tables, 'exit' to quit: ").lower()
        if action == "create":
            manager.create_health_data_tables()
        elif action == "drop":
            manager.drop_user_lookup_tables()
        elif action == "exit":
            manager.close_connection()
            break
        else:
            print("Invalid action. Please choose 'create', 'drop', or 'exit'.")

