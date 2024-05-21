# staging/get_organization_status.py

import sys
import os
import json

from syntrillo.healthie.forms import HealthieAPIForms

# Load environment variables from .env file
dotenv_path = ".env.staging"

forms_api = HealthieAPIForms(dotenv_path=dotenv_path)

# Create a custom module form with all parameters
form_name = "New Form"
charting = True
program = False
external_id = "12345"
external_id_type = "external_system"
is_video = False
on_completion_ifs_tag_id = "completion_tag_1"
prefill = False

response_form = forms_api.create_custom_module_form(
    name=form_name,
    use_for_charting=charting,
    use_for_program=program,
    external_id=external_id,
    external_id_type=external_id_type,
    is_video=is_video,
    on_completion_ifs_tag_id=on_completion_ifs_tag_id,
    prefill=prefill
)

print(json.dumps(response_form, indent=4))

form_id = response_form['createCustomModuleForm']['customModuleForm']['id']
print(form_id)


# Add a CustomModule to a CustomModuleForm with specified parameters
# form_id = "1143157"  # Replace with the ID of the CustomModuleForm
label = "Question 1"
mod_type = "text"
index = 0
is_custom = False
external_id = "67890"
external_id_type = "external_system"
options = ""
parent_custom_module_id = None
required = True
sublabel = "Please provide your answer"

response_module = forms_api.create_custom_module(
    custom_module_form_id=form_id,
    label=label,
    mod_type=mod_type,
    index=index,
    is_custom=is_custom,
    external_id=external_id,
    external_id_type=external_id_type,
    options=options,
    parent_custom_module_id=parent_custom_module_id,
    required=required,
    sublabel=sublabel
)

print(json.dumps(response_module, indent=4))

