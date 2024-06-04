import os
import json
import ast
import pandas as pd

# ----------------------------------------------------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------------------------------------------------
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

# ----------------------------------------------------------------------------------------------------------------
# SYNTRILLO QUESTIONNAIRE
# ----------------------------------------------------------------------------------------------------------------
class XLSXQuestionnaire():
    def __init__(self, xlsx_file_path):
        self.xlsx_file_path = xlsx_file_path

    def metadata(self):
        try:
            xls_metadata = pd.read_excel(self.xlsx_file_path, sheet_name='metadata', na_values=['', 'NaN'], header=None)
        except FileNotFoundError:
            raise FileNotFoundError(f"Excel file '{self.xlsx_file_path}' not found.")
        except Exception as e:
            raise Exception(f"Error reading Excel file: {str(e)}")

        # Convert DataFrame to a dictionary of key-value pairs
        metadata_dict = {}
        key = None
        for index, row in xls_metadata.iterrows():
            if pd.notna(row[0]):  # Check if column A (key) is not NaN
                key = row[0]  # Set the key
                metadata_dict[key] = row[1]  # Add key-value pair to the dictionary

        return metadata_dict

    def variables(self):
        try:
            xls_variables = pd.read_excel(self.xlsx_file_path, sheet_name='variables', na_values=['', 'NaN'])
        except FileNotFoundError:
            raise FileNotFoundError(f"Excel file '{self.xlsx_file_path}' not found.")
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

        return json_data_variables

    def to_json(self):
        return {
            'metadata' : self.metadata(),
            'variables' : self.variables()
        }

    def to_json_questionnaire(self):
        return JSONQuestionnaire(self.to_json())

class JSONQuestionnaire():
    def __init__(self, json_object=None):
        self.json = json_object
    
    def load(self, json_file_path):
        with open(json_file_path, 'r') as json_file:
            json_data = json.load(json_file)
        self.json = json_data

    def variables(self):
        return self.json["variables"]     

    def to_json(self):
        return self.json
    
    def to_healthie_form(self):
        return HealthieForm(self)

# ----------------------------------------------------------------------------------------------------------------
# HEALTHIE FORM
# ----------------------------------------------------------------------------------------------------------------
class HealthieFormItem():
    def __init__(self, json_item):
        self.json_item = json_item
    
    def options(self):
        if self.json_item["values"] is not None:
            options = "\n".join(self.json_item["values"])  # Join values with newline separator
        else:
            options = None
        return options
    
    def to_healthie_format(self):
        return {
            "external_id":  self.json_item["internal_name"],
            "label":        self.json_item["question"],
            "sublabel":     self.json_item["user_description"],
            "mod_type":     self.json_item["display"],
            # "options_array": item["values"] # not supported by Healthie
            "options":      self.options()  # Use "options" instead of "options_array"
        }
    
class HealthieForm():
    def __init__(self, json_questionnaire):
        self.json_questionnaire = json_questionnaire

    def items(self): # O.L. Why the term item, why not call that a module?
        items=[]
        for item in self.json_questionnaire.variables():
            items.append(HealthieFormItem(item))
        return items
    
    def custom_modules(self):           
        healthie_custom_modules = []

        for item in self.items():
            healthie_custom_modules.append(item.to_healthie_format())

        return healthie_custom_modules

    def push_to_healthie_platform(self):
        # TO implement
        pass

# ----------------------------------------------------------------------------------------------------------------
# UNIT TESTS
# ----------------------------------------------------------------------------------------------------------------
import unittest

class TestXLSXQuestionnaire(unittest.TestCase):

    def setUp(self):
        self.xlsx_questionnaire = XLSXQuestionnaire("./onboarding_nurse.xlsx")

    def test_xlsx_questionnaire_contains_metadata(self):
        self.assertEqual({
        'name': 'Onboarding Charting Note for Nurses', 
        'internal_name': 'onboarding_nurse', 
        'type': 'Charting Notes (for providers)', 
        'description': 'This is the onboarding questionnaire filled-up by nurses'
        },self.xlsx_questionnaire.metadata())

    def test_xlsx_questionnaire_contains_variables(self):
        self.assertEqual({
        'internal_name': 'form_title', 
        'question': 'On boarding questionnaire for nurses', 
        'display': 'label', 
        'special_values': None, 
        'values': None, 
        'add_unknown': None, 
        'add_not_applicable': None, 
        'user_description': None, 
        'type': None, 
        'LLM_prompt': None, 
        'comment': None}, self.xlsx_questionnaire.variables()[0])

    def test_xlsx_questionnaire_to_json_contains_metadata(self):
        self.assertEqual(self.xlsx_questionnaire.metadata(), self.xlsx_questionnaire.to_json()["metadata"])

    def test_xlsx_questionnaire_to_json_contains_variables(self):
        self.assertEqual(self.xlsx_questionnaire.variables(), self.xlsx_questionnaire.to_json()["variables"])

class TestHealthieFormContent(unittest.TestCase):

    def setUp(self):
        xlsx_questionnaire = XLSXQuestionnaire("./onboarding_nurse.xlsx")
        self.clinician_form = xlsx_questionnaire.to_json_questionnaire().to_healthie_form()

        # OR ...
        # json_questionnaire = JSONQuestionnaire()
        # json_questionnaire.load("./onboarding_nurse.json")
        # self.clinician_form = json_questionnaire.to_healthie_form()

    def test_syntrillio_clinician_form_contains_form_title(self):
        self.assertEqual({
        "external_id": "form_title",
        "label": "On boarding questionnaire for nurses",
        "sublabel": None,
        "mod_type": "label",
        "options": None
        }, self.clinician_form.custom_modules()[0])

    def test_syntrillio_clinician_form_contains_age(self):
        self.assertEqual({
        "external_id": "age",
        "label": "Age (years)",
        "sublabel": None,
        "mod_type": "number",
        "options": None
        }, self.clinician_form.custom_modules()[1])

    def test_syntrillio_clinician_form_contains_gender(self):
        self.assertEqual(    {
        "external_id": "gender",
        "label": "Sex at birth",
        "sublabel": None,
        "mod_type": "horizontal_radio",
        "options": "Male\nFemale\nunknown"
        }, self.clinician_form.custom_modules()[2])

    def test_syntrillio_clinician_form_contains_stroke_prior__independent_walking(self):
        self.assertEqual({
        "external_id": "stroke_prior__independent_walking",
        "label": "Independent walking prior to stroke",
        "sublabel": None,
        "mod_type": "horizontal_radio",
        "options": "yes\nno\nunknown\nnot applicable"
        }, self.clinician_form.custom_modules()[3])

    def test_syntrillio_clinician_form_contains_stroke_prior__use_assistive_device(self):
        self.assertEqual({
        "external_id": "stroke_prior__use_assistive_device",
        "label": "Use of assistive devices prior to stroke",
        "sublabel": None,
        "mod_type": "horizontal_radio",
        "options": "yes\nno\nunknown\nnot applicable"
        }, self.clinician_form.custom_modules()[4])

    def test_syntrillio_clinician_form_contains_health_goal(self):
        self.assertEqual({
        "external_id": "health_goal",
        "label": "What is your most important health goal?",
        "sublabel": None,
        "mod_type": "text",
        "options": None
        }, self.clinician_form.custom_modules()[5])

    def test_syntrillio_clinician_form_contains_stroke_risk_factors(self):
        self.assertEqual({
        "external_id": "stroke_risk_factors",
        "label": "Which risk factors for stroke do you have or have had in the past? (Select all that apply)",
        "sublabel": None,
        "mod_type": "checkbox",
        "options": "High blood pressure\nDiabetes\nHigh cholesterol levels\nSmoking\nFamily history of stroke\nHeart disease or atrial fibrillation\nunknown"
        }, self.clinician_form.custom_modules()[6])

    def test_syntrillio_clinician_form_contains_stroke_impact_physical_walking(self):
        self.assertEqual({
        "external_id": "stroke_impact_physical_walking",
        "label": "Impact of stroke- physical - Difficulty with walking",
        "sublabel": None,
        "mod_type": "radio",
        "options": "Strongly Disagree\nDisagree\nNeutral\nAgree\nStrongly Agree\nunknown"
        }, self.clinician_form.custom_modules()[7])

if __name__ == '__main__':

    unittest.main()

 