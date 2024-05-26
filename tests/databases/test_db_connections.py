# Path: ./tests/databases/test_db_connections.py

import unittest
from syntrillo.databases_management.connection import create_connection
import MySQLdb

class TestConnection(unittest.TestCase):

    def setUp(self):
        """Set up a database connection before each test."""
        self.conn, self.tunnel = create_connection(verbose=True)
        if self.conn is None:
            self.fail("Failed to create a database connection in setUp.")
        self.cursor = self.conn.cursor()

    def tearDown(self):
        """Close the database connection after each test."""
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
        if hasattr(self, 'tunnel') and self.tunnel:
            self.tunnel.stop()

    def test_create_connection(self):
        """Test if the connection to the MySQL database is established."""
        self.assertIsNotNone(self.conn, "Failed to create a database connection.")

    def test_temporary_table_operations(self):
        """Test creation, adding record, and deletion of a temporary table."""
        create_temp_table = """
        CREATE TEMPORARY TABLE temp_table (
            id INT AUTO_INCREMENT PRIMARY KEY,
            data VARCHAR(255)
        );
        """
        insert_record = "INSERT INTO temp_table (data) VALUES ('test_data');"
        select_record = "SELECT data FROM temp_table WHERE data='test_data';"
        drop_temp_table = "DROP TEMPORARY TABLE IF EXISTS temp_table;"

        try:
            # Create the temporary table
            self.cursor.execute(create_temp_table)
            self.conn.commit()

            # Insert a record into the temporary table
            self.cursor.execute(insert_record)
            self.conn.commit()

            # Select the record to verify insertion
            self.cursor.execute(select_record)
            result = self.cursor.fetchone()
            self.assertIsNotNone(result, "Failed to insert and retrieve record from temporary table.")
            self.assertEqual(result[0], 'test_data', f"Data mismatch: Expected 'test_data', got {result[0]}")

            # Drop the temporary table
            self.cursor.execute(drop_temp_table)
            self.conn.commit()

        except MySQLdb.OperationalError as e:
            self.fail(f"OperationalError: {e}")
        except MySQLdb.Error as e:
            self.fail(f"MySQL Error: {e}")
        except Exception as e:
            self.fail(f"Unexpected Error: {e}")

if __name__ == '__main__':
    unittest.main()
