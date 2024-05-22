# ./Syntrillo_Clinic/sources/syntrillo/data/structures/data_structure.py
#
# Define a class (DataStructure) to represent the data structure with attributes
#   - get
#   - can be used to QC data
#

import sys
import os

# add this folder to system path so that local modules can be imported
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

import json
from structures.storage_manager import StorageManager

class DataStructure:

    data = []
    healthie_custom_modules = []

    def __init__(self, storage_manager):
        self.storage_manager = storage_manager
        self.data = None

    def load_from_storage(self, filename):
        try:
            self.data = self.storage_manager.retrieve_json(filename)
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON file '{filename}.json' not found.")
        except Exception as e:
            raise Exception(f"Error loading JSON file: {str(e)}")

    def transform_for_healthie_api(self):
        if self.data is None:
            raise ValueError("No JSON data loaded. Call load_from_storage() first.")

        healthie_custom_modules = []
        for item in self.data['variables']:

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


# Example usage:
if __name__ == "__main__":

    # Initialize StorageManager
    storage_manager = StorageManager()

    # Initialize DataStructure
    data_structure = DataStructure(storage_manager)

    # Load JSON data from StorageManager
    filename = "onboarding_clinician"
    data_structure.load_from_storage(filename)

    # Transform JSON data for Healthie API
    healthie_custom_modules = data_structure.transform_for_healthie_api()

    # Print transformed data (or perform further actions)
    print(json.dumps(healthie_custom_modules, indent=4))
