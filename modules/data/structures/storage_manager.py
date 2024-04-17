#
#  Create a class (StorageManager) that handles parsing, QCing, storing, versioning, and retrieving DataStructure
#
# - parses and validates xls files into JSON structures in ./storage
# - stores and retreives json structures in ./storage
#

import pandas as pd
import math
import json
import os
import ast

def parse_comma_separated_string(s):
    if "'" in s:
        # String contains single quotes, use ast.literal_eval
        return list(ast.literal_eval(s))
    else:
        # String does not contain single quotes, split and strip
        return [part.strip() for part in s.split(',')]

def nan2null(value):
    """Transform NaN values to null."""
    if pd.isna(value):  # Check if value is NaN using pandas.isna
        return None  # Return None (which will be serialized to null in JSON)
    else:
        return value  # Return the original value if it's not NaN

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
            xls_data = pd.read_excel(xls_file_path, sheet_name='variables', na_values=['', 'NaN'])
        except FileNotFoundError:
            raise FileNotFoundError(f"Excel file '{xls_file_path}' not found.")
        except Exception as e:
            raise Exception(f"Error reading Excel file: {str(e)}")

        # Replace NaN values with None in the DataFrame
        xls_data = xls_data.where(pd.notnull(xls_data), None)

        # Convert Excel data to JSON format
        json_data = []
        for _, row in xls_data.iterrows():

            # Handle None value for 'values'
            if pd.isna(row['values']):  # Check for NaN (which is equivalent to None in pandas)
                cleaned_values = None
            else:
                # Preprocess values string to replace non-standard single quotes
                cleaned_values = str(row['values']).replace('‘', "'").replace('’', "'")

            # Use ast.literal_eval to transform the cleaned values string into a list
            if row['special_values'] == 'yes/no':
                values_list = ['yes', 'no']
            else:
                if cleaned_values is not None:
                    values_list = parse_comma_separated_string(cleaned_values)
                else:
                    values_list = None

            data = {
                'internal_name': nan2null(row['internal_name']),
                'question': nan2null(row['question']),
                'display': nan2null(row['display']),
                'special_values': nan2null(row['special_values']),
                'values': values_list,
                'user_description': nan2null(row['user_description']),
                'type': nan2null(row['type']),
                'LLM_prompt': nan2null(row['LLM_prompt']),
                'comment': nan2null(row['comment']),
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

