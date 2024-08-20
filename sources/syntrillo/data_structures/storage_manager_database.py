# Path: ./sources/syntrillo/data_structures/storage_manager_database.py

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

    Data structures are stored as JSON and the Excel file as a MEDIUMBLOB in the database.
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

    def list_all_structures(self) -> list:
        """
        Lists all available data structures.

        Returns a list of dictionaries with the following keys:
        - 'id': The unique identifier of the structure.
        - 'platform': The platform where the structure is used. (eg healthie_staging, healthie_production)
        - 'structure_name': The name of the structure.
        - 'structure_version': The version of the structure.
        - 'structure_full_name': The concatenation of the structure name and version, which is used as the base filename.
        """
        query = f"SELECT id, platform, name, version FROM {self.HEALTHIE_QUESTIONNAIRES_TABLE}"
        cursor = self.conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()

        data_structures = [
            {
                'id': result[0],
                'platform': result[1],
                'structure_name': result[2],
                'structure_version': result[3],
                'structure_full_name': f"{result[2]}_{result[3]}"
            }
            for result in results
        ]

        return data_structures

    def retrieve_structure_by_platform_name_and_version(
        self,
        platform: str,
        structure_name: str,
        structure_version: str,
        ) -> Tuple[dict, dict]:
        """
        Retrieves a specific data structure.

        Returns a tuple with the following elements:
        - The data structure as a dictionary.
        - A log dictionary with the following keys:
            - 'success': True if the data structure was successfully retrieved, False otherwise.
            - 'error': An error message if an error occurred, None otherwise

        Args:
            platform (str): The platform where the structure is used.
            structure_name (str): The name of the structure to be retrieved.
            structure_version (str): The version of the structure to be retrieved.
        """
        log = {
            'success': True,
        }
        query = f"""
        SELECT structure_json
        FROM {self.HEALTHIE_QUESTIONNAIRES_TABLE}
        WHERE platform = '{platform}' AND name = '{structure_name}' AND version = '{structure_version}'
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()

        if result is None:
            log['success'] = False
            log['error'] = f"Data structure '{structure_name}' version '{structure_version}' not found."
            return None, log
        else:
            try:
                structure_json = json.loads(result[0])
                return structure_json, log
            except json.JSONDecodeError as e:
                log['success'] = False
                log['error'] = f"Error decoding JSON data: {str(e)}"
                return None, log

    def retrieve_structure_by_id(
        self,
        id: int,
        ) -> Tuple[dict, dict]:
        """
        Retrieves a specific data structure.

        Returns a tuple with the following elements:
        - The data structure as a dictionary.
        - A log dictionary with the following keys:
            - 'success': True if the data structure was successfully retrieved, False otherwise.
            - 'error': An error message if an error occurred, None otherwise

        Args:
            id (int): The id of the structure to be retrieved.

        """
        log = {
            'success': True,
            'error': None
        }
        query = f"""
        SELECT structure_json FROM {self.HEALTHIE_QUESTIONNAIRES_TABLE}
        WHERE id = %s
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (id,))
        result = cursor.fetchone()
        cursor.close()

        if result is None:
            log['success'] = False
            log['error'] = f"Data structure with ID '{id}' not found."
            return None, log
        else:
            try:
                structure_json = json.loads(result[0])
                return structure_json, log
            except json.JSONDecodeError as e:
                log['success'] = False
                log['error'] = f"Error decoding JSON data: {str(e)}"
                return None, log

    def retrieve_excel_file_by_id(
        self,
        id: int,
        ) -> Tuple[dict, dict]:
        """
        Retrieves a specific excel file.

        Returns a tuple with the following elements:
        - The excel file.
        - Its full name.
        - A log dictionary with the following keys:
            - 'success': True if the data structure was successfully retrieved, False otherwise.
            - 'error': An error message if an error occurred, None otherwise

        Args:
            id (int): The id of the structure to be retrieved.

        """
        log = {
            'success': True,
            'error': None
        }
        query = f"""
        SELECT excel_file, name, version
        FROM {self.HEALTHIE_QUESTIONNAIRES_TABLE}
        WHERE id = %s
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (id,))
        result = cursor.fetchone()
        cursor.close()

        if result is None:
            log['success'] = False
            log['error'] = f"Data structure with ID '{id}' not found."
            return None, None, log
        else:
            full_name = f"{result[1]}_v{result[2]}.xlsx"
            return result[0], full_name, log



    def list_all_structures_with_metadata(self) -> list:
        """
        Lists all available data structures with metadata.

        Returns:
        - List[dict]: List of dictionaries with metadata information.
        """
        query = f"SELECT id, platform, name, version, structure_json FROM {self.HEALTHIE_QUESTIONNAIRES_TABLE}"
        cursor = self.conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()

        structure_list = []
        for id, platform, name, version, structure_json in results:
            json_data = json.loads(structure_json)
            metadata = json_data.get('metadata', {})
            structure_list.append({
                'id': id,
                'platform': platform,
                'structure_name': name,
                'structure_version': version,
                'metadata': metadata,
                'number_of_items': len(json_data.get('variables', [])),
                'number_of_variables': json_data.get('number_of_variables', ''),
                'created_at_est': convert_to_est(json_data.get('created_at', ''))
            })

        return structure_list

    def store_structure(
        self,
        platform: str,
        structure_name: str,
        structure_version: str,
        data_structure: dict,
        excel_file: bytes = None,
        delete_existing: bool = False,
        ) -> dict:
        """
        Stores a data structure in the database.

        Returns a log dictionary with the following keys:
        - 'success': True if the data structure was successfully stored, False otherwise.
        - 'messages': A list of messages detailing the operation.
        - 'structure_id': The ID of the stored structure.

        Args:
            - platform (str): The platform where the structure is used.
            - structure_name (str): The name of the structure to be stored.
            - structure_version (str): The version of the structure to be stored.
            - data_structure (dict): The data structure to be stored into structure_json.
            - excel_file (bytes): The Excel file to be stored into the database.
            - delete_existing (bool): Whether to delete an existing structure with the same name and version.

        Returns:
            log (dict): A log dictionary

        """
        log = {
            'success': True,
            'messages': []
            }

        if delete_existing:
            delete_query = f"""
            DELETE FROM {self.HEALTHIE_QUESTIONNAIRES_TABLE}
            WHERE platform = %s AND name = %s AND version = %s
            """
            cursor = self.conn.cursor()
            cursor.execute(delete_query, (platform, structure_name, structure_version))
            deleted_rows = cursor.rowcount  # Get the number of rows deleted
            self.conn.commit()
            cursor.close()

            if deleted_rows > 0:
                log['messages'].append(f"Deleted {deleted_rows} existing structure(s) in platform '{platform}' with name '{structure_name}' and version '{structure_version}'.")
            else:
                log['messages'].append(f"No existing structure found in platform '{platform}' with name '{structure_name}' and version '{structure_version}' to delete.")

        # Validate data structure
        if 'metadata' not in data_structure:
            log['success'] = False
            log['error'] = "Data structure must include metadata."
            return log
        if 'items' not in data_structure:
            log['success'] = False
            log['error'] = "Data structure must include items."
            return log

        structure_json = json.dumps(data_structure)

        try:
            # store the structure and excel file
            query = f"""
            INSERT INTO {self.HEALTHIE_QUESTIONNAIRES_TABLE} (platform, name, version, structure_json, excel_file)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor = self.conn.cursor()
            cursor.execute(query, (platform, structure_name, structure_version, structure_json, excel_file))
            self.conn.commit()
            # Retrieve the id of the newly inserted row
            log['structure_id'] = int(cursor.lastrowid)
            cursor.close()
        except pymysql.err.IntegrityError as e:
            log['success'] = False
            log['error'] = f"Error storing data structure: {e}"
            return log
        except Exception as e:
            log['success'] = False
            log['error'] = f"Unexpected error storing data structure: {e}"
            return log

        return log





# Example usage
if __name__ == '__main__':
    storage_manager = DatabaseStorageManagerDatabase()

    # Example data structure to store
    data_structure = {
        'metadata': {
            'title': 'Health Questionnaire',
            'description': 'A health questionnaire for tracking patient data.',
            'author': 'Research Department',
        },
        'items': [
            {'name': 'age', 'type': 'integer'},
            {'name': 'weight', 'type': 'float'},
            {'name': 'height', 'type': 'float'},
            {'name': 'blood_pressure', 'type': 'string'},
        ],
        'number_of_variables': 4,
        'created_at': '2024-08-14T12:00:00Z',
    }

    # Simulate an Excel file as a random byte array of ~1MB
    excel_file_simulated = os.urandom(1024 * 1024)  # 1 MB of random bytes

    # Store the data structure in the database
    log = storage_manager.store_structure(
        platform='healthie_staging',
        structure_name='health_questionnaire',
        structure_version='v1.0',
        data_structure=data_structure,
        excel_file=excel_file_simulated,
        delete_existing=True  # To overwrite if the same structure exists
    )

    # Check if the storing was successful
    if log['success']:
        print(f"Data structure stored successfully. Log: {log}")
    else:
        print(f"Failed to store data structure. Log: {log}")

    # List all stored data structures
    structures_list = storage_manager.list_all_structures()
    for structure in structures_list:
        print(f"ID: {structure['id']}, Name: {structure['structure_name']}, Version: {structure['structure_version']}, Full Name: {structure['structure_full_name']}")

    # Retrieve a specific data structure by its ID (assuming you know the ID)
    structure_id = structures_list[0]['id']  # Just as an example, using the first ID in the list
    retrieved_structure, retrieval_log = storage_manager.retrieve_structure_by_id(structure_id)

    # Check if retrieval was successful
    if retrieval_log['success']:
        print(f"Retrieved data structure: {json.dumps(retrieved_structure, indent=4)}")
    else:
        print(f"Failed to retrieve data structure. Log: {retrieval_log}")

