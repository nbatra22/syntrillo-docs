# Path: ./sources/syntrillo/data_structures/storage_manager.py

import pandas as pd
import math
import json
import os
import ast
from glob import glob


class StorageManager: # TODO : rename to DataStructureQuestionnaireParser and add a DataStructureStorageManager class
    """
    A class that handles parsing, QCing, storing, versioning, and retrieving DataStructure

    Data structures are defined in Excel xlsx files that can be handled easily by clinicians

    This class parses and validates xls files into JSON structures in the local ./storage folder of this repository

    These JSON files are used by the Healthie modules to build Charting Notes and Intake Forms

    """


    # Special values for some types of questions
    SPECIAL_VALUES = {
        'yes/no': ['yes', 'no'],
        'LikertAgreement_3values': ['Disagree', 'Neutral', 'Agree'],
        'LikertAgreement_5values': ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'],
        'LikertLikelihhod_3values': ['Unlikely', 'Neutral', 'Likely'],
        'LikertLikelihood_5values': ['Very Unlikely', 'Unlikely', 'Neutral', 'Likely', 'Very Likely'],
        'Assistance_level': ['Independent', 'Supervised', 'Min assist', 'Mod assist', 'Max assist', 'Total assist']
    }

    HEALTHIE_ALLOWED_DISPLAYS = {
        'text' : 'Open Answer(Short)',
        'textarea' : 'Open Answer(Long)',
        'checkbox' : 'Multiple Choice, Multiple Selection',
        'radio': 'Multiple Choice, Single Selection – vertical',
        'horizontal_radio': 'Multiple Choice, Single Selection – horizontal',
        'dropdown': 'Multiple Choice, Single Selection – Drop down list',
        'date' : 'Date',
        'date_picker': 'Date Picker',
        'time': 'Time',
        'number': 'Number',
        'label': 'used to display a title (no data retrieved)'
    }


    def __init__(self):
        # Get directory of the script where this class is defined
        self.script_dir = os.path.dirname(os.path.abspath(__file__))

        # defines the local storage area
        self.storage_path = os.path.join(self.script_dir, "storage")

        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)

    @staticmethod
    def parse_comma_separated_string(s: str) -> list:
        """
        Parse a comma-separated string into a list of strings.

        Args:
            s (str): Comma-separated string to parse.

        Returns:
            List[str]: List of strings.
        """
        if "'" in s:
            # String contains single quotes, use ast.literal_eval
            return list(ast.literal_eval(s))
        else:
            # String does not contain single quotes, split and strip
            return [part.strip() for part in s.split(',')]

    @staticmethod
    def nan2null(value: any) -> any:
        """
        Transform NaN values to null.

        Args:
            value (any): Value to transform.

        Returns:
            any: Transformed value.

        """
        if pd.isna(value):  # Check if value is NaN using pandas.isna
            return None  # Return None (which will be serialized to null in JSON)
        else:
            return value  # Return the original value if it's not NaN


    def parse_xlsx_to_json(self, xlsx_file_name: str) -> dict:
        """
        Excel to JSON parser.

        Parses an Excel file to a JSON data structure.

        This code has to be run manually to parse the Excel file to JSON, and store the JSON file in the repository.

        The Excel file is expected to have at least 2 tabs:
        - metadata : where high level information is defined for this structure
        - variables : list of variables and their characteristics

        It works with xls and xlsx files, but xlsx files prefered because of compatibility with Google ecosystem

        Args:
            xlsx_file_name (str): the Excel filename to be found in ./storage

        Returns:
            dict: JSON data structure with metadata and variables

        """
        # Construct full path to the Excel file
        xlsx_file_path = os.path.join(self.storage_path, xlsx_file_name)

        # --------------------------------
        # Load Excel file -- metadata tab
        # expected keys are: name, internal_name, type, description, version

        # ---
        # Check if the Excel file exists and load the metadata tab
        try:
            xls_metadata = pd.read_excel(xlsx_file_path, sheet_name='metadata', na_values=['', 'NaN'], header=None)
        except FileNotFoundError:
            raise FileNotFoundError(f"Excel file '{xlsx_file_path}' not found.")
        except Exception as e:
            raise Exception(f"Error reading Excel file: {str(e)}")

        # ---
        # Convert DataFrame to a dictionary of key-value pairs
        metadata_dict = {}
        key = None
        for index, row in xls_metadata.iterrows():
            if pd.notna(row[0]):  # Check if column A (key) is not NaN
                key = row[0]  # Set the key
                # lowercase the key
                key = key.lower()
                # replace spaces with underscores
                key = key.replace(' ', '_')
                metadata_dict[key] = row[1]  # Add key-value pair to the dictionary

        # ---
        # verify that the metadata dictionary has the expected keys
        expected_keys = ['name', 'internal_name', 'type', 'description', 'version']
        for key in expected_keys:
            if key not in metadata_dict:
                raise ValueError(f"Key '{key}' not found in metadata tab of Excel file '{xlsx_file_name}'")

        # ---
        # verify that the version matches the xls filename
        #  : version is for example '0.1' , and file name is 'onboarding_v0.1.xlsx'
        version = metadata_dict['version']
        # get the version from the filename : string betwen '_v' and '.xlsx'
        version_from_filename = xlsx_file_name.split('_v')[1].split('.xlsx')[0]
        if version != version_from_filename:
            raise ValueError(f"Version '{version}' in metadata tab does not match the version in the filename '{version_from_filename}'")


        # --------------------------------
        # Load Excel file -- variables tab
        try:
            xls_variables = pd.read_excel(xlsx_file_path, sheet_name='variables', na_values=['', 'NaN'])
        except FileNotFoundError:
            raise FileNotFoundError(f"Excel file '{xlsx_file_path}' not found.")
        except Exception as e:
            raise Exception(f"Error reading Excel file: {str(e)}")

        # ---
        # Column names QC

        # make column names lowercase
        xls_variables.columns = xls_variables.columns.str.lower()
        # replace spaces with underscores
        xls_variables.columns = xls_variables.columns.str.replace(' ', '_')

        # if it exists, rename 'question_item' to 'question'
        if 'question_item' in xls_variables.columns:
            xls_variables.rename(columns={'question_item': 'question'}, inplace=True)

        # verify that the columns are as expected
        expected_columns = ['internal_name', 'question', 'display', 'special_values', 'values', 'add_unknown', 'add_not_applicable', 'add_other', 'add_comment_box',   'user_description', 'type', 'llm_prompt', 'comment']
        for column in expected_columns:
            if column not in xls_variables.columns:
                raise ValueError(f"Column '{column}' not found in variables tab of Excel file '{xlsx_file_name}'")

        # ---
        # Replace NaN values with None in the DataFrame
        xls_variables = xls_variables.where(pd.notnull(xls_variables), None)

        # ---
        # Convert Excel data to JSON format
        json_data_variables = []
        for _, row in xls_variables.iterrows():

            # Handle None value for 'values'
            if pd.isna(row['values']):  # Check for NaN (which is equivalent to None in pandas)
                cleaned_values = None
            else:
                # Preprocess values string to replace non-standard single quotes
                cleaned_values = str(row['values']).replace('‘', "'").replace('’', "'")

            # loop through special values and create a list of values
            values_list = None
            for special_value, special_list in self.SPECIAL_VALUES.items():
                if row['special_values'] == special_value:
                    values_list = special_list
                    break

            # check collison between values and special values
            if values_list is not None and cleaned_values is not None:
                raise ValueError(f"Values and special values are both defined for variable '{row['internal_name']}'")

            # ---
            # Handle None value for 'values'
            if values_list is None:
                if cleaned_values is not None:
                    values_list = self.parse_comma_separated_string(cleaned_values)
                else:
                    values_list = None

            # ---
            if values_list is not None:
                if row['add_unknown'] == 'yes':
                    values_list.append('unknown')
                if row['add_not_applicable'] == 'yes':
                    values_list.append('not applicable')

            # ---
            # verify that row['display'] is in the allowed displays keys
            if row['display'] not in self.HEALTHIE_ALLOWED_DISPLAYS:
                raise ValueError(f"Display value '{row['display']}' not found in allowed displays for variable '{row['internal_name']}'")

            # ---
            # Create a dictionary for the data variable
            data_variable = {
                'internal_name': self.nan2null(row['internal_name']),
                'question': self.nan2null(row['question']),
                'display': self.nan2null(row['display']),
                'special_values': self.nan2null(row['special_values']),
                'values': values_list,
                'add_unknown': self.nan2null(row['add_unknown']),
                'add_not_applicable': self.nan2null(row['add_not_applicable']),
                'user_description': self.nan2null(row['user_description']),
                'type': self.nan2null(row['type']),
                'llm_prompt': self.nan2null(row['llm_prompt']),
                'comment': self.nan2null(row['comment']),
            }
            json_data_variables.append(data_variable)

            # ---
            # add other question if needed
            if row['add_other'] == 'yes':
                data_variable_other = {
                    'internal_name': f"{row['internal_name']}_other",
                    'question': f"Other {row['question']}",
                    'display': 'text',
                    'special_values': None,
                    'values': None,
                    'add_unknown': None,
                    'add_not_applicable': None,
                    'user_description': f"Please specify other {row['question']}",
                    'type': 'text',
                    'llm_prompt': None,
                    'comment': None,
                }
                json_data_variables.append(data_variable_other)

            # ---
            # add comment box if needed
            if row['add_comment_box'] == 'yes':
                data_variable_comment = {
                    'internal_name': f"{row['internal_name']}_comment",
                    'question': f"Comment for {row['question']}",
                    'display': 'textarea',
                    'special_values': None,
                    'values': None,
                    'add_unknown': None,
                    'add_not_applicable': None,
                    'user_description': f"Please add a comment for {row['question']}",
                    'type': 'text',
                    'llm_prompt': None,
                    'comment': None,
                }
                json_data_variables.append(data_variable_comment)


        # ---
        # Return JSON data structure
        json_data_structure = {
            'metadata': metadata_dict,
            'variables': json_data_variables
        }

        return json_data_structure


    def store_json(self, json_data: dict, filename: str) -> None:
        """
        Store JSON data to a file in the storage folder.

        Args:
            json_data (dict): JSON data to store.
            filename (str): Filename to use for the JSON file (without extension).

        Returns:
            None

        """
        # Construct full path to the JSON file
        json_file_path = os.path.join(self.storage_path, f"{filename}.json")

        # Save JSON data to file
        with open(json_file_path, 'w') as json_file:
            json.dump(json_data, json_file, indent=4)

    def retrieve_json(self, filename: str) -> dict:
        """
        Retrieve JSON data from a file in the storage folder.
        """
        # Construct full path to the JSON file
        json_file_path = os.path.join(self.storage_path, f"{filename}.json")

        # Load JSON data from file
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as json_file:
                json_data = json.load(json_file)
            return json_data
        else:
            raise FileNotFoundError(f"JSON file '{filename}.json' not found.")


    def parse_all_xlsx_files(self) -> None:
        """
        Will loop through all xlsx files in the storage folder and produce JSON structures.

        JSON structures will be stored in the storage folder.

        """

        # Loop through all .xlsx files in storage_path
        for filename in glob(os.path.join(self.storage_path, '*.xlsx')):
            # Parse XLSX file to JSON
            json_data = self.parse_xlsx_to_json(filename)

            # Remove .xlsx extension from filename
            filename_without_extension = os.path.splitext(filename)[0]

            # Store JSON data
            self.store_json(json_data, filename=filename_without_extension)

            print(filename)

    def list_all_structures(self) -> list:
        """
        Gives a list of all available JSON structures in self.storage_path

        Returns:
            List[dict]: List of dictionaries with 'filename' (without extension) and 'metadata' of each structure.

        """
        structure_list = []

        # Loop through all files in storage_path
        for filename in os.listdir(self.storage_path):
            if filename.endswith(".json"):  # Check if the file is a JSON file
                # Remove extension to get the filename
                structure_name = os.path.splitext(filename)[0]

                # Retrieve metadata from the JSON file
                try:
                    json_data = self.retrieve_json(structure_name)
                    metadata = json_data.get('metadata', {})  # Get metadata from JSON data
                    structure_list.append(
                        {
                            'filename': filename,
                            'structure_name': structure_name,
                            'metadata': metadata
                            }
                        )
                except FileNotFoundError:
                    # Handle the case where the JSON file cannot be found
                    print(f"Warning: JSON file '{structure_name}.json' not found.")

        return structure_list



# Example usage:
if __name__ == "__main__":

    # Initialize StorageManager
    storage_manager = StorageManager()

    if True:
        # xls_file_name = "onboarding.xlsx"
        xls_file_name = "telemed_OT_charting_note_v0.1.xlsx"
        json_data = storage_manager.parse_xlsx_to_json(xls_file_name)
        print(json.dumps(json_data, indent=4, default=str))

        if True:
            # Remove .xlsx extension from filename
            filename = os.path.splitext(xls_file_name)[0]

            # Store JSON data
            storage_manager.store_json(json_data, filename=filename)

            # Retrieve JSON data
            retrieved_data = storage_manager.retrieve_json(filename=filename)
            print(retrieved_data)


    if False:
        storage_manager.parse_all_xlsx_files()

        all_structures = storage_manager.list_all_structures()
        print(json.dumps(all_structures, indent=4))




