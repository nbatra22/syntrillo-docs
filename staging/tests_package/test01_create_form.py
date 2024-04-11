# staging/get_organization_status.py

import sys
import os
import json

# Add the modules root directory to sys.path
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)


from modules.healthie.forms import HealthieAPIForms

# Load environment variables from .env file
dotenv_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../.env")

forms_api = HealthieAPIForms(dotenv_path=dotenv_path)

if False:
    try:
        # Create a custom module form with all parameters
        form_name = "New Form"
        charting = True
        program = False
        external_id = "12345"
        external_id_type = "external_system"
        is_video = False
        on_completion_ifs_tag_id = "completion_tag_1"
        prefill = False

        response = forms_api.create_custom_module_form(
            form_name,
            charting,
            program,
            external_id=external_id,
            external_id_type=external_id_type,
            is_video=is_video,
            on_completion_ifs_tag_id=on_completion_ifs_tag_id,
            prefill=prefill
        )

        # Check if response is valid and contains data

        if response:
            print(json.dumps(response, indent=4))

        else:
            print("Failed to create custom module form.")

    except ValueError as ve:
        print(f"ValueError: {ve}")
        exit()

if True:

    try:
        # Add a CustomModule to a CustomModuleForm with specified parameters
        form_id = "1143157"  # Replace with the ID of the CustomModuleForm
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

        response = forms_api.create_custom_module(
            form_id,
            label,
            mod_type,
            index,
            is_custom=is_custom,
            external_id=external_id,
            external_id_type=external_id_type,
            options=options,
            parent_custom_module_id=parent_custom_module_id,
            required=required,
            sublabel=sublabel
        )

        if response:
            print(json.dumps(response, indent=4))

        else:
            print("Failed to create custom module form.")

    except ValueError as ve:
        print(f"ValueError: {ve}")
        exit()