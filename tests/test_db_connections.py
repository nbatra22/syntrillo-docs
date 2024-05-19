# tests/test_db_connections.py

import sys
import os

# add this folder to system path so that local modules can be imported
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

import unittest
from modules.databases.pseudonym_management.connection import create_connection

class TestConnection(unittest.TestCase):
    def test_create_connection(self):
        """Test if the connection to the MySQL database is established."""
        conn = create_connection(verbose=True)
        self.assertIsNotNone(conn, "Failed to create a database connection.")
        if conn:
            conn.close()

if __name__ == '__main__':
    unittest.main()
