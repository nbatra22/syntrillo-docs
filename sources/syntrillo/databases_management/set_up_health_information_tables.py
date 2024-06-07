# Path: ./sources/syntrillo/databases_management/set_up_health_information_tables.py
import MySQLdb
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

    def create_misc_health_data_table(self):
        """
        Create the 'misc_health_data' table if it does not exist.
        """

        create_table_query = """
        CREATE TABLE IF NOT EXISTS misc_health_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            syntrillo_internal_key BINARY(16) NOT NULL,
            data JSON NOT NULL,
            date DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """

        try:
            self.cursor.execute(create_table_query)
            self.conn.commit()
            print("Table 'misc_health_data' created successfully.")
        except MySQLdb.Error as e:
            self.conn.rollback()
            print(f"Error creating table: {e}")

    def drop_misc_health_data_table(self):
        """
        Drop the 'misc_health_data' table with a warning.
        """

        confirm = input("Are you sure you want to drop the table 'misc_health_data'? This action cannot be undone (yes/no): ")
        if confirm.lower() == "yes":
            try:
                self.cursor.execute("DROP TABLE IF EXISTS misc_health_data;")
                self.conn.commit()
                print("Table 'misc_health_data' dropped successfully.")
            except MySQLdb.Error as e:
                self.conn.rollback()
                print(f"Error dropping table: {e}")
        else:
            print("Skipping drop for table 'misc_health_data'.")

    def report_tables_status(self):
        """
        Report if the 'misc_health_data' table exists and its number of records.
        """
        try:
            self.cursor.execute("SELECT COUNT(*) FROM misc_health_data;")
            count = self.cursor.fetchone()[0]
            print(f"Table 'misc_health_data' exists with {count} records.")
        except MySQLdb.Error as e:
            print(f"Table 'misc_health_data' does not exist or cannot be accessed: {e}")

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

    # Report tables status
    manager.report_tables_status()

    while True:
        action = input("\nChoose an action: 'create' to create the 'misc_health_data' table, 'drop' to drop the 'misc_health_data' table, 'exit' to quit: ").lower()
        if action == "create":
            manager.create_misc_health_data_table()
        elif action == "drop":
            manager.drop_misc_health_data_table()
        elif action == "exit":
            manager.close_connection()
            break
        else:
            print("Invalid action. Please choose 'create', 'drop', or 'exit'.")
