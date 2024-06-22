# Path: ./sources/syntrillo/databases_management/set_up_health_information_tables.py
import pymysql
from syntrillo.databases_management.connection import DatabaseConnection

class HealthInformationTablesManager:
    """
    A class to manage the creation and deletion of health information tables in a MySQL database.
    """

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
        Create the PHI tables
        """

        create_misc_phi_table = """
        CREATE TABLE IF NOT EXISTS misc_health_data (
            id                          INT AUTO_INCREMENT PRIMARY KEY,
            syntrillo_internal_key      BINARY(16) NOT NULL,
            data_type VARCHAR(255)      NOT NULL,
            data_json                   JSON NOT NULL,
            date                        DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX (syntrillo_internal_key),
            INDEX (data_type)
        );
        """

        create_tenovi_raw_measurements_table = """
        CREATE TABLE IF NOT EXISTS tenovi_raw_measurements (
            id                          INT AUTO_INCREMENT PRIMARY KEY,
            syntrillo_internal_key      BINARY(16) NOT NULL,
            device_name                 VARCHAR(255) NOT NULL,
            metric_name                 VARCHAR(255) NOT NULL,
            value_1                     VARCHAR(255) DEFAULT NULL,
            value_2                     VARCHAR(255) DEFAULT NULL,
            timestamp_zulu              VARCHAR(255) NOT NULL,  -- this is timestamp (zulu time) from the device
            data_json                   JSON NOT NULL,
            date                        DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX (syntrillo_internal_key),
            INDEX (device_name)
        );
        """

        try:
            self.cursor.execute(create_misc_phi_table)
            self.cursor.execute(create_tenovi_raw_measurements_table)
            self.conn.commit()
            print("PHI tables created successfully.")
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"Error creating tables: {e}")

    def drop_user_lookup_tables(self):
        """
        Drop the user PHI tables interactively with a warning.

        Tables:
        - misc_health_data
        - tenovi_raw_measurements

        """
        tables = ["misc_health_data", "tenovi_raw_measurements"]
        for table in tables:
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
        tables = ["misc_health_data", "tenovi_raw_measurements"]
        for table in tables:
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

