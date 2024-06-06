# Path: ./sources/syntrillo/databases_management/logs.py

import MySQLdb
from syntrillo.databases_management.connection import DatabaseConnection
import json

def add_log_entry(event, json_data, comment):
    """
    Add an entry to the logs table.

    Args:
        event (str): A brief description of the event.
        json_data (dict): Additional data associated with the event in dictionary format.
        comment (str): Any additional comments about the log entry.
    """
    db_conn = DatabaseConnection(DatabaseConnection.PSEUDONYM_DB)
    conn, tunnel = db_conn.create_connection(verbose=True)
    if not conn:
        raise ConnectionError("Failed to connect to the database.")

    cursor = conn.cursor()

    add_log_query = """
    INSERT INTO logs (event, json_data, comment)
    VALUES (%s, %s, %s);
    """

    try:
        cursor.execute(add_log_query, (event, json.dumps(json_data), comment))
        conn.commit()
        print("Log entry added successfully.")
    except MySQLdb.Error as e:
        conn.rollback()
        print(f"Error adding log entry: {e}")
    finally:
        cursor.close()
        conn.close()
        if tunnel:
            tunnel.stop()
        print("Database connection closed.")

if __name__ == '__main__':
    # Example usage:
    event = "Test Event"
    json_data = {"key": "value"}
    comment = "This is a test log entry."
    add_log_entry(event, json_data, comment)
