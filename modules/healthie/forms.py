import os
import sys
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from healthie.base import HealthieAPI

class HealthieAPIForms(HealthieAPI):
    """
    A class extending HealthieAPI to handle forms-related operations.
    """

    def list_forms(
        self,
        include_default_templates: bool = False,
        active_status: bool = False,
        should_paginate: bool = False,
        category: str = None,
        keywords: str = None,
        offset: int = 0,
        sort_by: str = None
        ):
        """
        List forms based on the specified criteria using the Healthie API.
        See https://docs.gethealthie.com/docs/#listing-all-forms

        Parameters:
            include_default_templates (bool, optional): Whether to include default templates (default: False).
            active_status (bool, optional): Optional. Whether to fetch archived forms, false by default (default: False).
            should_paginate (bool, optional): Whether pagination should be enabled (default: False).
            category (str, optional): Filter forms by category (default: None). all, charting, program, intake
            keywords (str, optional): Keywords to search for in form names (default: None).
            offset (int, optional): Offset for pagination (default: 0).
            sort_by (str, optional): Field to use for sorting (default: None).

        Returns:
            dict: Response data containing the list of forms matching the specified criteria.
                  returns parts of the CustomModuleForm object "A template for a form, that can then be filled out"
                  : https://docs.gethealthie.com/schema/custommoduleform.doc
        """
        # Set up the GraphQL query to list custom module forms
        query = '''
            query formTemplates(
                $include_default_templates: Boolean,
                $active_status: Boolean,
                $should_paginate: Boolean,
                $category: String,
                $keywords: String,
                $offset: Int,
                $sortBy: String
            ) {
                customModuleForms(
                    include_default_templates: $include_default_templates,
                    active_status: $active_status,
                    should_paginate: $should_paginate,
                    category: $category,
                    keywords: $keywords,
                    offset: $offset,
                    sort_by: $sortBy
                ) {
                    id
                    is_video
                    name
                    prefill
                    uploaded_by_healthie_team
                    created_at
                    external_id
                    external_id_type
                    has_matrix_field
                    has_non_readonly_modules
                    updated_at
                    use_for_charting
                    use_for_program

                    custom_modules { id label } # "A question in a form template" : https://docs.gethealthie.com/schema/custommodule.doc

                }
            }
        '''

        # Set up the variables for the GraphQL query
        variables = {
            'include_default_templates': include_default_templates,
            'active_status': active_status,
            'should_paginate': should_paginate,
            'category': category,
            'keywords': keywords,
            'offset': offset,
            'sortBy': sort_by
        }

        try:
            # Make the GraphQL query request using the send_query method inherited from HealthieAPI
            response = self.send_query(query, variables)
            return response

        except Exception as e:
            print(f"An error occurred while listing forms: {str(e)}")
            return None

    def get_form_by_id(
        self,
        form_id: str = None,
        ):
        """
        List forms based on the specified criteria using the Healthie API.
        See https://docs.gethealthie.com/docs/#listing-all-forms

        Parameters:
            id (str, Required): The ID of the Form Template

        Returns:
            dict:   Returns a CustomModuleForm object, with all CustomModule objects
                  : https://docs.gethealthie.com/schema/custommoduleform.doc
                  : https://docs.gethealthie.com/schema/custommodule.doc
        """
        # Set up the GraphQL query to list custom module forms
        query = '''
            query form($id: ID) {
                customModuleForm(id: $id) {
                    id
                    is_video
                    name
                    prefill
                    uploaded_by_healthie_team
                    created_at
                    external_id
                    external_id_type
                    has_matrix_field
                    has_non_readonly_modules
                    updated_at
                    use_for_charting
                    use_for_program

                    # "A question in a form template" : https://docs.gethealthie.com/schema/custommodule.doc
                    custom_modules {
                        id
                        external_id         # Custom column used by API users. Used to relate our form objects with objects in third-party systems
                        external_id_type    # Custom column used by API users. Used to relate our form objects with objects in third-party systems
                        label               # The label of the question
                        sublabel            # The sublabel (description) of the question
                        is_custom           # Whether this module is a custom module
                        mod_type            # The type of question
                        # options
                        options_array       # The default options for this question, broken up into an array
                        position            # The position of the question (the lower the earlier the question is shown)
                        required            # Whether this question is required to be completed before the form it's in can be saved
                    }
                }
            }
        '''

        # Set up the variables for the GraphQL query
        variables = {'id': form_id}

        try:
            # Make the GraphQL query request using the send_query method inherited from HealthieAPI
            response = self.send_query(query, variables)
            return response.get('data', {}).get('customModuleForm', None)

        except Exception as e:
            print(f"An error occurred while retrieving the form: {str(e)}")
            return None


    def create_custom_module_form(
        self,
        name: str,
        use_for_charting: bool,
        use_for_program: bool,
        external_id: str = None,
        external_id_type: str = None,
        is_video: bool = False,
        on_completion_ifs_tag_id: str = None,
        prefill: bool = False
    ):
        """
        Create a custom module form using the Healthie API.

        Parameters:
            name (str): The name of the custom module form.
            use_for_charting (bool): Indicates if the form is used for charting.
            use_for_program (bool): Indicates if the form is used for a program.
            external_id (str, optional): External ID for relating form objects with third-party systems.
            external_id_type (str, optional): Type of external ID.
            is_video (bool, optional): Indicates if the form is a video module.
            on_completion_ifs_tag_id (str, optional): Tag ID for on-completion actions.
            prefill (bool, optional): Indicates if the form should be prefilled.

        Returns:
            dict: Response data containing the ID of the created custom module form and messages.
        """
        # Set up the GraphQL mutation to create a custom module form
        mutation = '''
            mutation createCustomModuleForm(
                $name: String,
                $use_for_charting: Boolean,
                $use_for_program: Boolean,
                $external_id: String,
                $external_id_type: String,
                $is_video: Boolean,
                $on_completion_ifs_tag_id: String,
                $prefill: Boolean
            ) {
                createCustomModuleForm(input: {
                    name: $name,
                    use_for_charting: $use_for_charting,
                    use_for_program: $use_for_program,
                    external_id: $external_id,
                    external_id_type: $external_id_type,
                    is_video: $is_video,
                    on_completion_ifs_tag_id: $on_completion_ifs_tag_id,
                    prefill: $prefill
                }) {
                    customModuleForm {
                        id
                    }
                    messages {
                        field
                        message
                    }
                }
            }
        '''

        # Set up the variables for the GraphQL mutation
        variables = {
            'name': name,
            'use_for_charting': use_for_charting,
            'use_for_program': use_for_program,
            'external_id': external_id,
            'external_id_type': external_id_type,
            'is_video': is_video,
            'on_completion_ifs_tag_id': on_completion_ifs_tag_id,
            'prefill': prefill
        }

        try:
            # Make the GraphQL mutation request using the send_query method inherited from HealthieAPI
            response = self.send_query(mutation, variables)
            return response.get('data', {}).get('createCustomModuleForm', None)

        except Exception as e:
            print(f"An error occurred while creating the custom module form: {str(e)}")
            return None

    def create_custom_module(
        self,
        custom_module_form_id: str,
        label: str,
        mod_type: str,
        index: int,
        is_custom: bool = False,
        external_id: str = None,
        external_id_type: str = None,
        options: str = None,
        parent_custom_module_id: str = None,
        required: bool = False,
        sublabel: str = None
    ):
        """
        Create a CustomModule within a CustomModuleForm using the Healthie API.

        Parameters:
            custom_module_form_id (str): The ID of the CustomModuleForm to which the CustomModule will be added.
            label (str): The label or name of the CustomModule.
            mod_type (str): The type of the CustomModule.
            index (int): The position index of the CustomModule within the form.
            is_custom (bool, optional): Indicates if the CustomModule is custom.
            external_id (str, optional): External ID for relating CustomModules with third-party systems.
            external_id_type (str, optional): Type of external ID.
            options (str, optional): Options for the CustomModule (e.g., for dropdowns).
            parent_custom_module_id (str, optional): ID of the parent CustomModule if this is a nested CustomModule.
            required (bool, optional): Indicates if the CustomModule is required.
            sublabel (str, optional): Sublabel or additional description for the CustomModule.

        Returns:
            dict: Response data containing the ID of the created CustomModule and messages.
        """
        # Set up the GraphQL mutation to create a CustomModule
        mutation = '''
            mutation createCustomModule(
                $custom_module_form_id: String!,
                $label: String!,
                $mod_type: String!,
                $index: Int!,
                $is_custom: Boolean,
                $external_id: String,
                $external_id_type: String,
                $options: String,
                $parent_custom_module_id: String,
                $required: Boolean,
                $sublabel: String
            ) {
                createCustomModule(input: {
                    custom_module_form_id: $custom_module_form_id,
                    label: $label,
                    mod_type: $mod_type,
                    index: $index,
                    is_custom: $is_custom,
                    external_id: $external_id,
                    external_id_type: $external_id_type,
                    options: $options,
                    parent_custom_module_id: $parent_custom_module_id,
                    required: $required,
                    sublabel: $sublabel
                }) {
                    customModule {
                        id
                    }
                    messages {
                        field
                        message
                    }
                }
            }
        '''

        # Set up the variables for the GraphQL mutation
        variables = {
            'custom_module_form_id': custom_module_form_id,
            'label': label,
            'mod_type': mod_type,
            'index': index,
            'is_custom': is_custom,
            'external_id': external_id,
            'external_id_type': external_id_type,
            'options': options,
            'parent_custom_module_id': parent_custom_module_id,
            'required': required,
            'sublabel': sublabel
        }

        try:
            # Make the GraphQL mutation request using the send_query method inherited from HealthieAPI
            response = self.send_query(mutation, variables)
            return response

        except Exception as e:
            print(f"An error occurred while creating the custom module form: {str(e)}")
            return None




if __name__ == "__main__":
    # Example usage of the list_forms function
    dotenv_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/.env")
    forms_api = HealthieAPIForms(dotenv_path=dotenv_path)

    # tests
    try:
        # List all forms
        response = forms_api.list_forms(sort_by='name_asc', keywords='Scoring')
        print(json.dumps(response, indent=4))

        # Retrieve a form 1138897
        response = forms_api.get_form_by_id('1138897')
        print(json.dumps(response, indent=4))


    except ValueError as ve:
        print(f"ValueError: {ve}")
        exit()
