# ./Syntrillo_Clinic/tests/healthie/staging/tests_package/test04_data_structure_create_form.py

import sys
import os
import json

from syntrillo.healthie.forms import HealthieAPIForms
from syntrillo.data.structures.data_structure import DataStructure
from syntrillo.data.structures.storage_manager import StorageManager

# --------------------------------------------------------
# initialize Healthie API

# Load environment variables from .env file
dotenv_path = ".env.Healthie.staging"

forms_api = HealthieAPIForms(dotenv_path=dotenv_path)

# --------------------------------------------------------
# Initialize StorageManager

storage_manager = StorageManager()

# Initialize DataStructure
data_structure = DataStructure(storage_manager)

# Load JSON data from StorageManager
filename = "onboarding"
data_structure.load_from_storage(filename)

# Transform JSON data for Healthie API
modules = data_structure.transform_for_healthie_api()

# Print transformed data (or perform further actions)
print(json.dumps(modules, indent=4))



# Call the create_form_wrapper function to create a new form with the specified modules
form_name = 'Sample Form - Onboarding'
use_for_charting = True
use_for_program = False

# Assuming 'healthie_api' is an instance of your HealthieAPI class
response = forms_api.create_form_wrapper(
    form_name=form_name,
    use_for_charting=use_for_charting,
    use_for_program=use_for_program,
    modules=modules,
    external_id="sample_form_onboarding",
)

# Print the response data containing the form and modules
print(json.dumps(response, indent=4))



