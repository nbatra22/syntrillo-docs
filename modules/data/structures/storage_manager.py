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
from glob import glob

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

    def parse_xlsx_to_json(self, xlsx_file_name):
        # Construct full path to the Excel file
        xlsx_file_path = os.path.join(self.storage_path, xlsx_file_name)

        # --------------------------------
        # Load Excel file -- metadata
        try:
            xls_metadata = pd.read_excel(xlsx_file_path, sheet_name='metadata', na_values=['', 'NaN'], header=None)
        except FileNotFoundError:
            raise FileNotFoundError(f"Excel file '{xlsx_file_path}' not found.")
        except Exception as e:
            raise Exception(f"Error reading Excel file: {str(e)}")

        # Convert DataFrame to a dictionary of key-value pairs
        metadata_dict = {}
        key = None
        for index, row in xls_metadata.iterrows():
            if pd.notna(row[0]):  # Check if column A (key) is not NaN
                key = row[0]  # Set the key
                metadata_dict[key] = row[1]  # Add key-value pair to the dictionary

        # --------------------------------
        # Load Excel file -- variables
        try:
            xls_variables = pd.read_excel(xlsx_file_path, sheet_name='variables', na_values=['', 'NaN'])
        except FileNotFoundError:
            raise FileNotFoundError(f"Excel file '{xlsx_file_path}' not found.")
        except Exception as e:
            raise Exception(f"Error reading Excel file: {str(e)}")

        # Replace NaN values with None in the DataFrame
        xls_variables = xls_variables.where(pd.notnull(xls_variables), None)

        # Convert Excel data to JSON format
        json_data_variables = []
        for _, row in xls_variables.iterrows():

            # Handle None value for 'values'
            if pd.isna(row['values']):  # Check for NaN (which is equivalent to None in pandas)
                cleaned_values = None
            else:
                # Preprocess values string to replace non-standard single quotes
                cleaned_values = str(row['values']).replace('‘', "'").replace('’', "'")

            # Use ast.literal_eval to transform the cleaned values string into a list
            if row['special_values'] == 'yes/no':
                values_list = ['yes', 'no']
            elif row['special_values'] == 'LikertAgreement_3values':
                values_list = ['Disagree', 'Neutral', 'Agree']
            elif row['special_values'] == 'LikertAgreement_5values':
                values_list = ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree']
            elif row['special_values'] == 'LikertLikelihhod_3values':
                values_list = ['Unlikely', 'Neutral', 'Likely']
            elif row['special_values'] == 'LikertLikelihood_5values':
                values_list = ['Very Unlikely', 'Unlikely', 'Neutral', 'Likely', 'Very Likely']
            else:
                if cleaned_values is not None:
                    values_list = parse_comma_separated_string(cleaned_values)
                else:
                    values_list = None

            if values_list is not None:
                # TODO : deal with add unknown and add not_applicable
                if row['add_unknown'] == 'yes':
                    values_list.append('unknown')
                if row['add_not_applicable'] == 'yes':
                    values_list.append('not applicable')


            data_variable = {
                'internal_name': nan2null(row['internal_name']),
                'question': nan2null(row['question']),
                'display': nan2null(row['display']),
                'special_values': nan2null(row['special_values']),
                'values': values_list,
                'add_unknown': nan2null(row['add_unknown']),
                'add_not_applicable': nan2null(row['add_not_applicable']),
                'user_description': nan2null(row['user_description']),
                'type': nan2null(row['type']),
                'LLM_prompt': nan2null(row['LLM_prompt']),
                'comment': nan2null(row['comment']),
            }
            json_data_variables.append(data_variable)

        return {
            'metadata' : metadata_dict,
            'variables' : json_data_variables
        }


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

def run_all_xlsx_files():
    """
    Will loop through all xlsx files in the ./storage folder and produce JSON structures
    """

    # Get directory of the script where this class is defined
    script_dir = os.path.dirname(os.path.abspath(__file__))
    storage_path = os.path.join(script_dir, "storage")

    # Initialize StorageManager
    storage_manager = StorageManager()

    # Loop through all .xlsx files in storage_path
    for filename in glob(os.path.join(storage_path, '*.xlsx')):
        # Parse XLSX file to JSON
        json_data = storage_manager.parse_xlsx_to_json(filename)

        # Remove .xlsx extension from filename
        filename_without_extension = os.path.splitext(filename)[0]

        # Store JSON data
        storage_manager.store_json(json_data, filename=filename_without_extension)


# Example usage:
if __name__ == "__main__":

    run_all_xlsx_files()

    """
    # Initialize StorageManager
    storage_manager = StorageManager()

    # Parse onboarding.xls to JSON
    #   works with xls and xlsx files
    #   xlsx files prefered because of compatibility with Google ecosystem
    xls_file_name = "onboarding.xlsx"  # Specify the name of your Excel file
    json_data = storage_manager.parse_xlsx_to_json(xls_file_name)

    # Store JSON data
    storage_manager.store_json(json_data, filename="onboarding")

    # Retrieve JSON data
    retrieved_data = storage_manager.retrieve_json(filename="onboarding")
    print(retrieved_data)
    """

