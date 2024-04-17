#
#  Create a class (StorageManager) that handles parsing, QCing, storing, versioning, and retrieving DataStructure
#
# - parses and validates xls files into JSON structures in ./storage
# - stores and retreives json structures in ./storage
#

import pandas as pd
import json
import os
import ast

class StorageManager:
    def __init__(self):
        # Get directory of the script where this class is defined
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.storage_path = os.path.join(self.script_dir, "storage")
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)

    def parse_xls_to_json(self, xls_file_name):
        # Construct full path to the Excel file
        xls_file_path = os.path.join(self.storage_path, xls_file_name)

        # Load Excel file
        try:
            xls_data = pd.read_excel(xls_file_path, sheet_name='variables')
        except FileNotFoundError:
            raise FileNotFoundError(f"Excel file '{xls_file_path}' not found.")
        except Exception as e:
            raise Exception(f"Error reading Excel file: {str(e)}")

        # Replace NaN values with empty strings
        xls_data.fillna('', inplace=True)

        # Convert Excel data to JSON format
        json_data = []
        for _, row in xls_data.iterrows():

            # Preprocess values string to replace non-standard single quotes
            cleaned_values = row['values'].replace('‘', "'").replace('’', "'")

            # Use ast.literal_eval to transform the cleaned values string into a list
            if row['special_values'] == 'yes/no':
                values_list = ['yes', 'no']
            else:
                values_list = ast.literal_eval(f"[{cleaned_values}]")

            data = {
                'internal_name': row['internal_name'],
                'question': row['question'],
                'display': row['display'],
                'special_values': row['special_values'],
                'values': values_list,
                'user_description': row['user_description'],
                'type': row['type'],
                'LLM_prompt': row['LLM_prompt'],
                'comment': row['comment']
            }
            json_data.append(data)

        return json_data

    def store_json(self, json_data, filename):
        # Construct full path to the JSON file
        json_file_path = os.path.join(self.storage_path, f"{filename}.json")

        # Save JSON data to file
        with open(json_file_path, 'w') as json_file:
            json.dump(json_data, json_file, indent=4)

    def retrieve_json(self, filename):
        # Construct full path to the JSON file
        json_file_path = os.path.join(self.storage_path, f"{filename}.json")

        # Load JSON data from file
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as json_file:
                json_data = json.load(json_file)
            return json_data
        else:
            raise FileNotFoundError(f"JSON file '{filename}.json' not found.")

# Example usage:
if __name__ == "__main__":
    # Initialize StorageManager
    storage_manager = StorageManager()

    # Parse onboarding.xls to JSON
    xls_file_name = "onboarding.xls"  # Specify the name of your Excel file
    json_data = storage_manager.parse_xls_to_json(xls_file_name)

    # Store JSON data
    storage_manager.store_json(json_data, filename="onboarding")

    # Retrieve JSON data
    retrieved_data = storage_manager.retrieve_json(filename="onboarding")
    print(retrieved_data)

