# Path: ./sources/syntrillo/data_structures/questionnaire_healthie_manager.py
# Path: ./sources/syntrillo/data_structures/data_structure.py

import sys
import os
import json

from typing import Tuple

from syntrillo.data_structures.storage_manager_local_file_system import DataStructureStorageManagerLocalFileSystem
from syntrillo.data_structures.storage_manager_database import DataStructureStorageManagerDatabase
from syntrillo.api_healthie.forms import HealthieForms

class DataStructureQuestionnaireHealthieManager:
    """

    Allows to load a JSON data structure from the file system or the database, transform it into a format suitable for the Healthie API, and create that questionnaire as a custom module into Healthie

    """

    def __init__(self):
        # Initialize storage managers and Healthie API
        self.storage_manager_local_file_system = DataStructureStorageManagerLocalFileSystem()
        self.storage_manager_database = DataStructureStorageManagerDatabase()
        self.forms_api = HealthieForms()

        # Initialize attributes
        self.structure_name = None
        self.structure_id = None
        self.structure = None
        self.healthie_custom_modules = None


    def load_structure_from_storage(self, structure_name: str) -> Tuple[dict, dict]:
        """
        loads a specific data structure from the file system storage manager

        stores in the structure attribute

        Returns a tuple : the structure and a log dictionary with the result of the operation

        Args:
            structure_name (str): name of the structure (name_version) to load and transform

        Returns:
            structure,log (Tuple[dict, dict]): the structure and a log dictionary with the result of the operation

        """

        self.structure_name = structure_name

        structure, log = self.storage_manager_local_file_system.retrieve_structure(structure_name)

        if log['success']:
            self.structure = structure

        return structure, log

    def load_structure_from_database(self, structure_id: int) -> Tuple[dict, dict]:
        """
        loads a specific data structure from the database storage manager

        stores in the structure attribute

        Returns the structure and a log dictionary with the result of the operation

        Args:
            structure_id (int): id of the structure to load and transform

        Returns:
            structure,log (Tuple[dict, dict]): the structure and a log dictionary with the result of the operation

        """

        self.structure_id = structure_id

        structure, log = self.storage_manager_database.retrieve_structure_by_id(structure_id)

        if log['success']:
            self.structure_name = structure.get('metadata').get('internal_name') + '_v' + structure.get('metadata').get('version')
            self.structure = structure

        return structure, log


    def transform_into_healthie_modules(self):
        """
        Tranforms the structure into a format suitable for the Healthie API

        """
        if self.structure is None:
            return None

        healthie_custom_modules = []
        for item in self.structure['items']:

            if item["values"] is not None:
                options = "\n".join(item["values"])  # Join values with newline separator
            else:
                options = None

            transformed_item = {
                "external_id": item["internal_name"],
                "label": item["question"],
                "sublabel": item["sublabel"],
                "mod_type": item["display"],
                # "options_array": item["values"] # not supported by Healthie
                "options": options  # Use "options" instead of "options_array"
            }
            healthie_custom_modules.append(transformed_item)

        self.healthie_custom_modules = healthie_custom_modules

        return healthie_custom_modules

    def create_healthie_form(self) -> dict:
        """
        Creates a new form in Healthie with the modules from the structure

        Returns a log dictionary with the result of the operation

        """

        # form name and (our) external id
        #  : form name have to be less than 50 characters
        metadata : dict = self.structure.get('metadata', {})
        form_name = metadata.get('name') + ' (v' + metadata.get('version') + ')'
        external_id_type = metadata.get('internal_name')  # name without version
        external_id = external_id_type + '_v' + metadata.get('version') # versioned name

        # form type
        use_for_charting = metadata.get('use_for_charting', False)
        use_for_program = metadata.get('use_for_program', False)

        # prefill flag
        prefill = metadata.get('prefill', False)

        # ----------- Error handling ---------------
        # check form name length
        if len(form_name) > 50:
            log = {
                "success": False,
                "message": "Error: Form name is too long",
                "structure_name" : self.structure_name,
                "metadata": self.structure.get('metadata'),
            }
            return log

        # error if version already in get('name')
        if metadata.get('version') in metadata.get('name'):
            log = {
                "success": False,
                "message": "Error: Version number should not be in the name",
                "structure_name" : self.structure_name,
                "metadata": self.structure.get('metadata'),
            }
            return log

        # error if version already in get('internal_name')
        if metadata.get('version') in metadata.get('internal_name'):
            log = {
                "success": False,
                "message": "Error: Version number should not be in the internal_name",
                "structure_name" : self.structure_name,
                "metadata": self.structure.get('metadata'),
            }
            return log

        # ----------- Create form ---------------
        # Call the create_form_wrapper function to create a new form with the specified modules
        response = self.forms_api.create_form_wrapper(
            form_name=form_name,
            external_id=external_id,
            external_id_type=external_id_type,
            use_for_charting=use_for_charting,
            use_for_program=use_for_program,
            prefill=prefill,
            modules=self.healthie_custom_modules,
        )

        if response is None:
            log = {
                "success": False,
                "message": "Error: Questionnaire form not created",
                "structure_name" : self.structure_name,
                "metadata": self.structure.get('metadata'),
            }
        else:
            log = {
                "success": True,
                "message": "Questionnaire form created successfully",
                "structure_name" : self.structure_name,
                "metadata": self.structure.get('metadata'),
            }

        return log

    def create_healthie_form_from_structure(self, structure_name: str) -> dict:
        """
        Creates a new form in Healthie with the modules from the structure

        Makes use of files stored in the local file system

        Returns a log dictionary with the result of the operation

        Args:
            structure_name (str): name of the structure (name_version) to load and transform

        """

        # load structure from storage
        _, log_load = self.load_structure_from_storage(structure_name)
        if not log_load['success']:
            return log_load

        # transform structure into Healthie format
        _ = self.transform_into_healthie_modules()

        # create Healthie form
        log_create = self.create_healthie_form()

        return log_create


    def create_healthie_form_from_structure_id(self, structure_id: id) -> dict:
        """
        Creates a new form in Healthie with the modules from the structure

        Makes use of entries in the database

        Returns a log dictionary with the result of the operation

        TODO : option to disallow same form name and version at Healthie (in production)

        Args:
            structure_name (str): name of the structure (name_version) to load and transform

        """

        # load structure from storage
        _, log_load = self.load_structure_from_database(structure_id)
        if not log_load['success']:
            return log_load

        # transform structure into Healthie format
        _ = self.transform_into_healthie_modules()

        # create Healthie form
        log_create = self.create_healthie_form()

        return log_create




# Example usage:
if __name__ == "__main__":
    pass
