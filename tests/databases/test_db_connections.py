# ./Syntrillo_Clinic/tests/databases/test_db_connections.py

import sys
import os

import unittest
from syntrillo.databases.pseudonym_management.connection import create_connection

class TestConnection(unittest.TestCase):
    def test_create_connection(self):
        """Test if the connection to the MySQL database is established."""
        conn = create_connection(verbose=True)
        self.assertIsNotNone(conn, "Failed to create a database connection.")
        if conn:
            conn.close()

if __name__ == '__main__':
    unittest.main()
