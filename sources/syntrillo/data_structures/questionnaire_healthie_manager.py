# Path: ./sources/syntrillo/data_structures/data_structure.py

import sys
import os
import json

from typing import Tuple

from syntrillo.data_structures.storage_manager import DataStructureStorageManager
from syntrillo.api_healthie.forms import HealthieForms

class DataStructureQuestionnaireHealthieManager:
    """
    Allows to transform a JSON data structure into a format suitable for the Healthie API, and create that questionnaire as a custom module into Healthie

    """

    structure_name = None
    structure = None
    healthie_custom_modules = None

    def __init__(self):
        self.storage_manager = DataStructureStorageManager()
        self.forms_api = HealthieForms()


    def load_structure_from_storage(self, structure_name: str) -> Tuple[dict, dict]:
        """
        loads a specific data structure from the storage manager

        stores in the structure attribute

        Returns the structure and a log dictionary with the result of the operation

        """

        self.structure_name = structure_name

        structure, log = self.storage_manager.retrieve_structure(structure_name)

        if log['success']:
            self.structure = structure

        return structure, log


    def transform_into_healthie_modules(self):
        """
        Tranforms the structure into a format suitable for the Healthie API

        """
        if self.structure is None:
            return None

        healthie_custom_modules = []
        for item in self.structure['variables']:

            if item["values"] is not None:
                options = "\n".join(item["values"])  # Join values with newline separator
            else:
                options = None

            transformed_item = {
                "external_id": item["internal_name"],
                "label": item["question"],
                "sublabel": item["user_description"],
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

        # form name and external id
        form_name = self.structure.get('metadata').get('name') + ' ( version ' + self.structure.get('metadata').get('version') + ' )'
        external_id = self.structure.get('metadata').get('internal_name')

        # form type
        use_for_charting = self.structure.get('metadata').get('use_for_charting', False)
        use_for_program = self.structure.get('metadata').get('use_for_program', False)

        # Call the create_form_wrapper function to create a new form with the specified modules
        response = self.forms_api.create_form_wrapper(
            form_name=form_name,
            external_id=external_id,
            use_for_charting=use_for_charting,
            use_for_program=use_for_program,
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

        Returns a log dictionary with the result of the operation

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


# Example usage:
if __name__ == "__main__":
    pass
