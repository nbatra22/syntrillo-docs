# staging/get_organization_status.py

import sys
import os
import json

from syntrillo.healthie.forms import HealthieAPIForms

# Load environment variables from .env file
dotenv_path = ".env.staging"

forms_api = HealthieAPIForms(dotenv_path=dotenv_path)

# Define the modules to be created within the form
modules = [
    {
        'label': 'Question 1',
        'mod_type': 'text',
        'required': True,
        'sublabel': 'Please answer this question'
    },
    {
        'label': 'Question 2',
        'mod_type': 'text',
    },
    {
        'label': 'Question 3',
        'mod_type': 'text',
    },
    {
        'label': 'Question 4',
        'mod_type': 'radio',
        'options': 'xxx\nyyy\nzzz',
    },
]

# Call the create_form_wrapper function to create a new form with the specified modules
form_name = 'Sample Form'
use_for_charting = True
use_for_program = False

# Assuming 'healthie_api' is an instance of your HealthieAPI class
response = forms_api.create_form_wrapper(
    form_name=form_name,
    use_for_charting=use_for_charting,
    use_for_program=use_for_program,
    modules=modules
)

# Print the response data containing the form and modules
print(json.dumps(response, indent=4))



