# Path: ./sources/syntrillo/databases_management/set-up_logs_table.py

import pymysql
from syntrillo_lib.databases_management.connection import DatabaseConnection

class LogsTableManager:
    """
    A class to manage the creation and deletion of the logs table in a MySQL database.
    The table stores logs with fields such as date, event, json_data, and comment.
    """

    def __init__(self):
        """
        Initialize the LogsTableManager by creating a database connection.
        """
        if __name__ != "__main__":
            raise RuntimeError("LogsTableManager class can only be instantiated interactively.")

        db_conn = DatabaseConnection(DatabaseConnection.PSEUDONYM_DB)
        self.conn, self.tunnel = db_conn.create_connection(verbose=True)
        if not self.conn:
            raise ConnectionError("Failed to connect to the database.")
        self.cursor = self.conn.cursor()

    def create_logs_table(self):
        """
        Create the logs table if it does not exist.

        The logs table stores log entries with fields:
        - date: The date and time of the log entry.
        - event: A brief description of the event.
        - json_data: Additional data associated with the event in JSON format.
        - comment: Any additional comments about the log entry.
        """
        create_logs_table = """
        CREATE TABLE IF NOT EXISTS logs (
            id INT AUTO_INCREMENT PRIMARY KEY,                      # Auto-increment ID for unique identification
            date DATETIME DEFAULT CURRENT_TIMESTAMP,                # Date and time of the log entry
            event VARCHAR(255) NOT NULL,                            # Brief description of the event
            json_data JSON,                                         # Additional data associated with the event in JSON format
            comment TEXT                                            # Additional comments about the log entry
        );
        """
        try:
            self.cursor.execute(create_logs_table)
            self.conn.commit()
            print("Logs table created successfully.")
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print(f"Error creating logs table: {e}")

    def drop_logs_table(self):
        """
        Drop the logs table interactively with a warning.

        Table:
        - logs: Stores log entries with fields such as date, event, json_data, and comment.
        """
        confirm = input("Are you sure you want to drop the table 'logs'? This action cannot be undone (yes/no): ")
        if confirm.lower() == "yes":
            try:
                self.cursor.execute("DROP TABLE IF EXISTS logs;")
                self.conn.commit()
                print("Table 'logs' dropped successfully.")
            except pymysql.MySQLError as e:
                self.conn.rollback()
                print(f"Error dropping table 'logs': {e}")
        else:
            print("Skipping drop for table 'logs'.")

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
    manager = LogsTableManager()

    while True:
        action = input("Choose an action: 'create' to create table, 'drop' to drop table, 'exit' to quit: ").lower()
        if action == "create":
            manager.create_logs_table()
        elif action == "drop":
            manager.drop_logs_table()
        elif action == "exit":
            manager.close_connection()
            break
        else:
            print("Invalid action. Please choose 'create', 'drop', or 'exit'.")
