# Path: ./sources/syntrillo/data_structures/xlsx_questionnaire_handler.py

import pandas as pd
import json
import html
import os
import ast
import io
from typing import Union, Tuple
from glob import glob
from datetime import datetime, timezone

from syntrillo_lib.data_structures.storage_manager_local_file_system import DataStructureStorageManagerLocalFileSystem
from syntrillo_lib.data_structures.storage_manager_database import DataStructureStorageManagerDatabase
from syntrillo_lib.system.local_environment_and_secrets import LocalEnvironmentAndSecrets


class DataStructureXlsxQuestionnaireHandler:
    """
    A class that handles parsing, QCing, storing, versioning, and retrieving DataStructure

    Data structures are defined in Excel xlsx files that can be handled easily by clinicians

    This class parses and validates xlsx files into JSON structures in the local ./storage folder of this repository

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

    # Allowed display types for Healthie questionaires
    #  : most are mod_type, which can be obtained by running api_healthie.forms.get_form_by_id on a form with all types of questions
    HEALTHIE_ALLOWED_DISPLAYS = {
        'text' : 'Open Answer(Short)',
        'textarea' : 'Open Answer(Long)',
        'checkbox' : 'Multiple Choice, Multiple Selection',
        'radio': 'Multiple Choice, Single Selection - vertical',
        'horizontal_radio': 'Multiple Choice, Single Selection - horizontal',
        'dropdown': 'Multiple Choice, Single Selection - Drop down list',
        'date' : 'Date',
        'date_picker': 'Date Picker',
        'time': 'Time',
        'number': 'Number',
        'label': 'used to display a title (no data retrieved)',
        'read_only': 'used to display a read-only *HTML* value (no data retrieved)',

        'html': 'not a mod_type. It is used to display a read-only mod_type *HTML* value (no data retrieved), but the html value is in the question item in Excel',

        # -- Charting bank questions, with specific mod_type, where values are displayed automatically across questionnaires
        'medications': 'Medications question from Charting bank',
        'name': 'Name question from Charting bank',
        'legal_name': 'Legal First Name question from Charting bank',
        'dob': 'Date of Birth question from Charting bank',
        'blood_pressure': 'Blood Pressure question from Charting bank',
        'Weight': 'Weight question from Charting bank',
        'Height (in.)': 'Height question from Charting bank',
        'synced_allergy': 'Allergy question from Charting bank',

        # -- mod_type related on our own metrics
        'StrokeRiskScore': 'Stroke Risk Score from our own metrics',
    }


    def __init__(self):
        # instantiate the storage managers
        self.storage_manager_local_file_system = DataStructureStorageManagerLocalFileSystem()
        self.storage_manager_database = DataStructureStorageManagerDatabase()

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


    def parse_xlsx_to_json(
        self,
        xlsx_file: Union[str, bytes],
        xlsx_filename: str = None,
        ) -> Tuple[dict, dict]:
        """
        Excel to JSON parser.

        Parses an Excel file to a JSON data structure.

        This code has to be run manually to parse the Excel file to JSON, and store the JSON file in the repository.

        The Excel file is expected to have at least 2 tabs:
        - metadata : where high level information is defined for this structure
        - variables : list of variables and their characteristics

        It works with xls and xlsx files, but xlsx files prefered because of compatibility with Google ecosystem

        It returns a tuple with two elements:
        - dict: JSON data structure with metadata and variables
        - log: Log dictionary with the following keys
            - 'success': True if the Excel file was successfully parsed, False otherwise.
            - 'error': An error message if an error occurred, None otherwise.

        Args:
            - xlsx_file (str|bytes): the Excel filename to be found in ./storage or the content of the file as bytes if coming from the database.
            - xlsx_filename (str): the filename of the xlsx file. Should be provided if xlsx_file is bytes.

        Returns:
            data_structure,log (dict, dict): The data structure as a dictionary and a log dictionary.

        """

        log = {
            'success': True,
        }

        # --------------------------------
        # manage the input xlsx_file
        if isinstance(xlsx_file, str):
            # if xlsx_file is string, it is a filename
            xlsx_file_io = os.path.join(self.storage_manager_local_file_system.storage_path, xlsx_file)
            xlsx_filename = xlsx_file
            self.xlsx_bytes = None
        elif isinstance(xlsx_file, bytes):
            # if xlsx_file is bytes, it is the content of the file
            xlsx_file_io = io.BytesIO(xlsx_file)
            self.xlsx_bytes = xlsx_file
            if xlsx_filename is None:
                log['success'] = False
                log['error'] = f"xlsx_filename should be provided if xlsx_file is bytes"
                return None, log
        else:
            log['success'] = False
            log['error'] = f"Excel file is not a string or bytes"
            return None, log

        # store as class variables
        self.xlsx_file_io = xlsx_file_io
        self.xlsx_filename = xlsx_filename

        # --------------------------------
        # Load Excel file -- metadata tab
        # expected keys are: name, internal_name, type, description, version

        # ---
        # Check if the Excel file exists and load the metadata tab
        try:
            xls_metadata = pd.read_excel(io = xlsx_file_io, sheet_name='metadata', na_values=['', 'NaN'], header=None)
        except FileNotFoundError:
            log['success'] = False
            log['error'] = f"Excel file not found."
            return None, log
        except Exception as e:
            log['success'] = False
            log['error'] = f"Error reading Excel file: {str(e)}"
            return None, log

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
        expected_keys = ['name', 'internal_name', 'type', 'description', 'prefill', 'version', 'addspace']
        for key in expected_keys:
            if key not in metadata_dict:
                log['success'] = False
                log['error'] = f"Key '{key}' not found in metadata tab of Excel file '{xlsx_filename}'"
                return None, log

        # ---
        # verify that the version matches the xls filename
        #  : version is for example '0.1' , and file name is 'onboarding_v0.1.xlsx'
        version = metadata_dict['version']
        # get the version from the filename : string betwen '_v' and '.xlsx'
        version_from_filename = xlsx_filename.split('_v')[1].split('.xlsx')[0]
        if version != version_from_filename:
            log['success'] = False
            log['error'] = f"Version '{version}' in metadata tab does not match the version in the filename '{version_from_filename}'"
            return None, log


        # ---
        # manage the form type
        if metadata_dict.get('type') == "Charting Notes (for providers)" :
            use_for_charting = True
            use_for_program = False
        elif metadata_dict.get('type') == "Intake Form (for patients)" :
            use_for_charting = False
            use_for_program = False
        elif metadata_dict.get('type') == "Intake Form (for patients) - Used in programs":
            use_for_charting = False
            use_for_program = True
        else:
            log['success'] = False
            log['error'] = f"Type '{metadata_dict.get('type')}' not recognized for Excel file '{xlsx_filename}'"

        # store the use_for_charting and use_for_program in the metadata
        metadata_dict['use_for_charting'] = use_for_charting
        metadata_dict['use_for_program'] = use_for_program

        # ---
        # manage prefill
        prefill_str = str(metadata_dict.get('prefill')).lower()
        if prefill_str == 'yes':
            metadata_dict['prefill'] = True
        elif prefill_str == 'no':
            metadata_dict['prefill'] = False
        else:
            log['success'] = False
            log['error'] = f"Prefill value '{metadata_dict.get('prefill')}' not recognized"

        # ---
        # add space after each question
        add_space_str = str(metadata_dict.get('addspace')).lower()
        if add_space_str == 'yes':
            add_space_after_question = True
        else:
            add_space_after_question = False

        # --------------------------------
        # Load Excel file -- variables tab
        try:
            xls_variables = pd.read_excel(xlsx_file_io, sheet_name='variables', na_values=['', 'NaN'])
        except FileNotFoundError:
            log['success'] = False
            log['error'] = f"Excel file not found."
            return None, log
        except Exception as e:
            log['success'] = False
            log['error'] = f"Error reading Excel file: {str(e)}"
            return None, log

        # ---
        # Column names QC

        # make column names lowercase
        xls_variables.columns = xls_variables.columns.str.lower()
        # replace spaces with underscores
        xls_variables.columns = xls_variables.columns.str.replace(' ', '_')

        # if it exists, rename 'question*' to 'question'
        for colname in xls_variables.columns:
            if colname.startswith('question'):
                xls_variables.rename(columns={colname: 'question'}, inplace=True)

        # verify that the columns are as expected
        expected_columns = ['internal_name', 'question', 'sublabel', 'display', 'special_values', 'values', 'add_unknown', 'add_not_available', 'add_not_applicable', 'add_other', 'add_comment_box', 'type', 'llm_prompt', 'internal_description', 'comment']
        for column in expected_columns:
            if column not in xls_variables.columns:
                log['success'] = False
                log['error'] = f"Column '{column}' not found in variables tab of Excel file "

        # ---
        # Replace NaN values with None in the DataFrame
        xls_variables = xls_variables.where(pd.notnull(xls_variables), None)

        # ---
        # Convert Excel data to JSON format
        json_data_items = []
        number_of_variables = 0
        for _, row in xls_variables.iterrows():

            # skip if 'display' is None
            if row['display'] is None or row['display'] == "" or pd.isna(row['display']):
                continue

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
                log['success'] = False
                log['error'] = f"Values and special values are both defined for variable '{row['internal_name']}'"
                return None, log

            # ---
            # Handle None value for 'values'
            if values_list is None:
                if cleaned_values is not None:
                    if row['display'] in ['text', 'textarea']:
                        # Escape special characters for HTML
                        values_list = [html.escape(cleaned_values)]
                    elif row['display'] == 'read_only':
                        # Use the raw value for read-only fields
                        #  : here, clean values can include html tags.
                        values_list = [cleaned_values]
                    else:
                        values_list = self.parse_comma_separated_string(cleaned_values)
                else:
                    values_list = None

            if row['display'] == 'html':
                # Use the question value for html fields
                values_list = [ row['question'] ]

            # ---
            if values_list is not None:
                if row['add_unknown'] == 'yes':
                    values_list.append('unknown')

                if row['add_not_available'] == 'yes':
                    values_list.append('not available')

                if row['add_not_applicable'] == 'yes':
                    values_list.append('not applicable')

            # ---
            # verify that row['display'] is in the allowed displays keys
            if row['display'] not in self.HEALTHIE_ALLOWED_DISPLAYS:
                log['success'] = False
                log['error'] = f"Display value '{row['display']}' not found in allowed displays for variable '{row['internal_name']}'"
                return None, log

            # ---
            # count if it is a variable
            if row['display'] not in ['label', 'read_only', 'html']:
                number_of_variables += 1

            # ---
            # Specific values for question and sublabel : 'space' and 'separator'
            question = self.nan2null(row['question'])
            sublabel = self.nan2null(row['sublabel'])

            if row['display'] in ['label', 'read_only']:
                # deal with blank question (used as a separator). Add a space character to avoid empty question
                if row['question'] == '' or row['question'] is None or pd.isna(row['question']) :
                    question = ' '

                if question == 'separator':
                    question = '- ' * 60
                elif question == 'space':
                    question = ' '

                if sublabel == 'space':
                    sublabel = ' '

            # ---
            # manage home made html type
            if row['display'] == 'html':
                display = 'read_only'
                question = ' '
            else:
                display = row['display']

            # ---
            # if display is checkbox, radio, horizontal_radio, dropdown : make sure values are defined
            if display in ['checkbox', 'radio', 'horizontal_radio', 'dropdown', 'read_only']:
                if values_list is None:
                    log['success'] = False
                    log['error'] = f"Values are not defined for variable '{row['internal_name']}'"
                    return None, log

            # ---
            # Create a dictionary for the data variable
            data_variable = {
                'internal_name': self.nan2null(row['internal_name']),
                'question': question,
                'sublabel': sublabel,
                'display': display,
                'special_values': self.nan2null(row['special_values']),
                'values': values_list,
                'add_unknown': self.nan2null(row['add_unknown']),
                'add_not_applicable': self.nan2null(row['add_not_applicable']),
                'type': self.nan2null(row['type']),
                'llm_prompt': self.nan2null(row['llm_prompt']),
                'internal_description': self.nan2null(row['internal_description']),
                'comment': self.nan2null(row['comment']),
            }
            json_data_items.append(data_variable)

            # ---
            # add other question if needed
            if row['add_other'] == 'yes':
                data_variable_other = {
                    'internal_name': f"{row['internal_name']}_other",
                    'question': f"Other {row['question']}",
                    'sublabel': f"Please specify other {row['question']}",
                    'display': 'text',
                    'special_values': None,
                    'values': None,
                    'add_unknown': None,
                    'add_not_applicable': None,
                    'type': 'text',
                    'llm_prompt': None,
                    'internal_description': None,
                    'comment': None,
                }
                json_data_items.append(data_variable_other)

            # ---
            # add comment box if needed
            if row['add_comment_box'] == 'yes':
                data_variable_comment = {
                    'internal_name': f"{row['internal_name']}_comment",
                    'question': f"Comment for {row['question']}",
                    'sublabel': f"Please add a comment for {row['question']}",
                    'display': 'textarea',
                    'special_values': None,
                    'values': None,
                    'add_unknown': None,
                    'add_not_applicable': None,
                    'type': 'text',
                    'llm_prompt': None,
                    'internal_description': None,
                    'comment': None,
                }
                json_data_items.append(data_variable_comment)

            if add_space_after_question:
                data_spacer = {
                    'internal_name': None,
                    'question': ' ',
                    'sublabel': None,
                    'display': 'label',
                    'special_values': None,
                    'values': None,
                    'add_unknown': None,
                    'add_not_applicable': None,
                    'type': 'text',
                    'llm_prompt': None,
                    'internal_description': None,
                    'comment': None,
                }
                json_data_items.append(data_spacer)


            # end of loop over rows

        # ---
        # Return JSON data structure
        json_data_structure = {
            'metadata': metadata_dict,
            'items': json_data_items,
            'number_of_variables': number_of_variables,
            'created_at': datetime.now(timezone.utc).isoformat()
        }

        # store as class variable
        self.json_data_structure = json_data_structure

        # validate json_data_structure
        try:
            # This will raise an exception if the dictionary is not JSON-serializable
            json.dumps(json_data_structure)
        except (TypeError, ValueError) as e:
            log['success'] = False
            log['error'] = f"Invalid JSON data structure: {str(e)}"

        return json_data_structure, log


    def store_json_structure(self, json_data: dict, structure_name: str) -> dict:
        """
        Store JSON data to a file in the storage folder.

        Args:
            json_data (dict): JSON data to store.
            structure_name (str): Filename to use for the JSON file (without extension).

        Returns:
        - dict: Log dictionary with the following keys:
           - 'success': True if the JSON data was successfully stored, False otherwise.
           - 'error': An error message if an error occurred, None otherwise.

        """

        log = self.storage_manager_local_file_system.store_structure(structure_name, json_data)

        return log

    def store_json_structure_in_database(
        self,
        delete_existing: bool = True
        ) -> dict:
        """
        Store JSON data to a file in the storage folder.

        Args:
            delete_existing (bool): True if the existing structure should be deleted, False otherwise.

        Returns:
        - dict: Log dictionary with the following keys:
           - 'success': True if the JSON data was successfully stored, False otherwise.
           - 'error': An error message if an error occurred, None otherwise.

        """

        # get the platform from the LocalEnvironmentAndSecrets
        secrets = LocalEnvironmentAndSecrets(load_healthie_secrets=True)
        platform = secrets.get_healthie_organization()

        log = self.storage_manager_database.store_structure(
            platform=platform,
            structure_name=self.json_data_structure['metadata']['internal_name'],
            structure_version=self.json_data_structure['metadata']['version'],
            data_structure=self.json_data_structure,
            excel_file=self.xlsx_bytes,
            delete_existing=delete_existing
        )

        return log


    def retrieve_json_structure(self, structure_name: str) -> Tuple[dict, dict]:
        """
        Retrieve JSON data from a file in the storage folder.

        Returns a tuple:
        - The data structure as a dictionary.
        - A log dictionary with the following keys:
            - 'success': True if the data structure was successfully retrieved, False otherwise.
            - 'error': An error message if an error occurred, None otherwise.
        """

        structure, log = self.storage_manager_local_file_system.retrieve_structure(structure_name)

        return structure, log


    def parse_all_xlsx_files(
        self,
        stop_on_error: bool = False
        ) -> None:
        """
        Will loop through all xlsx files in the storage folder and produce JSON structures.

        JSON structures will be stored in the storage folder.
        """

        overall_log = {
            'success': True,
        }

        # Loop through all .xlsx files in storage_path
        for filename in glob(os.path.join(self.storage_manager_local_file_system.storage_path, '*.xlsx')):
            # Parse XLSX file to JSON
            json_data, parse_log = self.parse_xlsx_to_json(filename)

            if parse_log['success'] :
                # Remove .xlsx extension from filename
                filename_without_extension = os.path.splitext(filename)[0]

                # Store JSON data
                store_log = self.store_json_structure(json_data, structure_name=filename_without_extension)

            store_log = None

            overall_log['filename'] = {
                                       'parse_log': parse_log,
                                       'store_log': store_log
                                       }

            if stop_on_error and ( not parse_log['success'] or not store_log['success'] ) :
                break

        return overall_log






# Usage:
if __name__ == "__main__":

    # Initialize StorageManager
    storage_manager = DataStructureXlsxQuestionnaireHandler()

    if True:
        # xls_file_name = "onboarding.xlsx"
        xls_file_name = "telemed_OT_charting_note_v0.1.xlsx"
        json_data, log1 = storage_manager.parse_xlsx_to_json(xls_file_name)
        print(json.dumps(json_data.get('metadata'), indent=4, default=str))

        if log1['success']:
            # Remove .xlsx extension from filename
            filename = os.path.splitext(xls_file_name)[0]

            # Store JSON data
            log2 = storage_manager.store_json_structure(json_data, structure_name=filename)

            if log2['success']:
                print('Success: JSON data stored successfully.')
            else:
                print(log2)
        else:
            print(log1)

    if False:
        storage_manager.parse_all_xlsx_files()

        all_structures = storage_manager.list_all_structures()
        print(json.dumps(all_structures, indent=4))




