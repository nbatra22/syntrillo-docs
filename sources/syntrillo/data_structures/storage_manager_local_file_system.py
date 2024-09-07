# Path: ./sources/syntrillo/data_structures/storage_manager_local_file_system.py

import os
import json
from typing import Tuple

from syntrillo.helper_functions.time import convert_to_est

class DataStructureStorageManagerLocalFileSystem:
    """
    Defines where the data structures are stored.

    Provides functions to list all available data structures, store and retrieve a specific one.

    Data structures are stored as json files in a specific directory.

    """

    # Relative path to the storage directory
    STORAGE_RELATIVE_PATH = 'storage'

    # Absolute path to the storage directory, defined when the class is instantiated
    storage_path = None

    def __init__(self) -> None:
        """
        Initializes the storage manager.

        Defines the storage path.

        Creates the storage directory if it does not exist.
        """

        # Get directory of the script where this class is defined
        self.script_dir = os.path.dirname(os.path.abspath(__file__))

        # defines the local storage area
        self.storage_path = os.path.join(self.script_dir, self.STORAGE_RELATIVE_PATH)

        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)

    def get_storage_path(self) -> str:
        """
        Returns the storage path.

        :return: The storage path.
        """

        return self.storage_path

    def list_all_structures(self) -> list:
        """
        Lists all available data structures.

        Returns a list of filenames (without extension) of the data structures.
        """

        data_structures = [os.path.splitext(f)[0] for f in os.listdir(self.storage_path) if f.endswith('.json')]

        return data_structures


    def retrieve_structure(self, structure_name: str) -> Tuple[dict, dict]:
        """
        Retrieves a specific data structure.

        For now, it is obtained from the JSON files stored in self.storage_path.

        TODO : consider moving JSON and XLSX to a database

        Args
        - structure_name: The name of the data structure to retrieve, including its version.

        Returns a tuple:
        - The data structure as a dictionary.
        - A log dictionary with the following keys:
            - 'success': True if the data structure was successfully retrieved, False otherwise.
            - 'error': An error message if an error occurred, None otherwise.

        """

        filename = structure_name + '.json'
        file_path = os.path.join(self.storage_path, filename)

        log = {
            'success': True,
        }

        data_structure = {}

        try:
            with open(file_path, 'r') as file:
                data_structure = json.load(file)
        except FileNotFoundError:
            log['success'] = False
            log['error'] = f"Data structure '{structure_name}' not found."
        except Exception as e:
            log['success'] = False
            log['error'] = f"Error loading data structure: {str(e)}"

        return data_structure, log


    def list_all_structures_with_metadata(self) -> list:
        """
        Gives a list of all available JSON structures in self.storage_path

        Returns:
        - List[dict]: List of dictionaries with
            - 'filename' (without extension)
            - 'structure_name'
            - 'metadata'
            - 'number_of_items', which is the number of variables and labels in the structure

        """
        structure_list = []

        # Loop through all files in storage_path
        for filename in os.listdir(self.storage_path):
            if filename.endswith(".json"):  # Check if the file is a JSON file
                # Remove extension to get the filename
                structure_name = os.path.splitext(filename)[0]

                # define Excel filename and check if it exists
                # TODO : then what?
                filename_xlsx = structure_name + '.xlsx'
                file_path_xlsx = os.path.join(self.storage_path, filename_xlsx)
                if not os.path.exists(file_path_xlsx):
                    file_path_xlsx = None

                # Retrieve metadata from the JSON file
                # TODO : manage log
                try:
                    json_data, _ = self.retrieve_structure(structure_name)
                    metadata = json_data.get('metadata', {})  # Get metadata from JSON data
                    structure_list.append(
                        {
                            'filename_json': filename,
                            'filename_xlsx': filename_xlsx,
                            'structure_name': structure_name,
                            'metadata': metadata,
                            'number_of_items': len(json_data.get('variables', [])),
                            'number_of_variables': json_data.get('number_of_variables', ''),
                            'created_at_est': convert_to_est(json_data.get('created_at', '')),
                            }
                        )
                except FileNotFoundError:
                    # Handle the case where the JSON file cannot be found
                    print(f"Warning: JSON file '{structure_name}.json' not found.")

        return structure_list


    def store_structure(self, structure_name: str, data_structure: dict) -> dict:
        """
        Stores a data structure.

        :param structure_name: The name of the data structure to store.
        :param data_structure: The data structure to store as a dictionary. It must include metadata and items

        Returns a log dictionary with the following keys:
        - 'success': True if the data structure was successfully stored, False otherwise.
        - 'error': An error message if an error occurred, None otherwise.

        """

        log = {
            'success': True,
        }

        # check if the data structure has metadata and items
        if 'metadata' not in data_structure:
            log['success'] = False
            log['error'] = "Data structure must include metadata."
            return log
        if 'items' not in data_structure:
            log['success'] = False
            log['error'] = "Data structure must include items."
            return log

        filename = structure_name + '.json'
        file_path = os.path.join(self.storage_path, filename)

        try:
            with open(file_path, 'w') as file:
                json.dump(data_structure, file, indent=4, default=str)
        except Exception as e:
            log['success'] = False
            log['error'] = f"Error storing data structure: {str(e)}"

        return log


if __name__ == '__main__':
    storage_manager = DataStructureStorageManagerLocalFileSystem()

    # print storage path
    print(storage_manager.storage_path)

    # list all structures
    print(storage_manager.list_all_structures())

    # list all structures with metadata
    structures = storage_manager.list_all_structures_with_metadata()
    print(json.dumps(structures, indent=4, default=str))

