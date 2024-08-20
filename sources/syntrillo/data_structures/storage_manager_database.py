# Path: ./sources/syntrillo/data_structures/database_storage_manager.py

import os
import json
import pymysql
from typing import Tuple

from syntrillo.databases_management.connection import DatabaseConnection
from syntrillo.databases_management.set_up_health_information_tables import HealthInformationTablesManager
from syntrillo.helper_functions.time import convert_to_est


class DatabaseStorageManagerDatabase:
    """
    Manages storage of data structures in a MySQL database.

    Provides functions to list all available data structures, store and retrieve a specific one.

    Data structures are stored as JSON and BLOB in the database.
    """

    # get name of the questionnaires table from the HealthInformationTablesManager
    HEALTHIE_QUESTIONNAIRES_TABLE = HealthInformationTablesManager.HEALTHIE_QUESTIONNAIRES_TABLE

    def __init__(self):
        """
        Initialize the DatabaseStorageManager by creating a database connection.
        """

        # connect to our database
        db_conn = DatabaseConnection(DatabaseConnection.HEALTH_INFO_DB)
        self.conn, _ = db_conn.create_connection()

    def get_storage_table_name(self) -> str:
        """
        Returns the name of the table where the data structures are stored.

        :return: The name of the table where the data structures are stored.
        """

        return self.HEALTHIE_QUESTIONNAIRES_TABLE

    """
    Manage name and version of the questionnaire (since version is included in the filename)

    """