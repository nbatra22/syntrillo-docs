# staging/get_organization_status.py

import sys
import os
import json


from syntrillo.healthie.forms import HealthieAPIForms

# Load environment variables from .env file
dotenv_path = ".env.staging"

forms_api = HealthieAPIForms(dotenv_path=dotenv_path, verbose=True)

# Define the modules to be created within the form
modules = [
    {
        'label': 'Question 1',
        'mod_type': 'text',
    },
    {
        'label': 'Question 2',
        'mod_type': 'text',
    },
    {
        'label': 'Question 3',
        'mod_type': 'text',
    }
]


# Create a custom module form
response_form = forms_api.create_custom_module_form(
    name = "New Form - testing modules",

)

print(json.dumps(response_form, indent=4))

form_id = response_form['createCustomModuleForm']['customModuleForm']['id']
print(form_id)

# -------------------------------



response_modules = forms_api.create_custom_modules(
    custom_module_form_id=form_id,
    custom_modules=modules
)

print(json.dumps(response_modules, indent=4))

