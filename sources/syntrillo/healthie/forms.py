# modules/healthy/forms.py

import os
import sys
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from healthie.utils import HealthieAPIUtils

class HealthieAPIForms(HealthieAPIUtils):
    """
    A class extending HealthieAPIUtils to handle forms-related operations.
    """

    def __init__(
        self,
        api_key: str = None,
        organization: str = 'staging',
        dotenv_path: str = None,
    ):
        super().__init__(api_key, organization, dotenv_path)


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
            dict: returns parts of the CustomModuleForm object "A template for a form, that can then be filled out"
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

                    # custom_modules { id label } # "A question in a form template" : https://docs.gethealthie.com/schema/custommodule.doc

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

        # Make the GraphQL query request using the send_query method inherited from HealthieAPI
        response = self.send_query(query, variables)

        return response

    def get_form_id_by_external_id(
        self,
        external_id: str = None,
        ):
        """
        Reteive a specific form by its id
        See https://docs.gethealthie.com/docs/#retrieving-a-form

        Parameters:
            external_id (str, Required): The ID of the Form Template

        Returns:
            list of customModuleForm ids
        """
        # Set up the GraphQL query to list custom module forms
        query = '''
            query formTemplates(
                $include_default_templates: Boolean,
                $active_status: Boolean,
                $should_paginate: Boolean,
                $category: String,
                $keywords: String,
                $offset: Int
            ) {
                customModuleForms(
                    include_default_templates: $include_default_templates,
                    active_status: $active_status,
                    should_paginate: $should_paginate,
                    category: $category,
                    keywords: $keywords,
                    offset: $offset
                ) {
                    id
                    external_id
                }
            }
            '''

        # Set up the variables for the GraphQL query
        variables = { }

        # Make the GraphQL query request using the send_query method inherited from HealthieAPI
        response = self.send_query(query, variables)

        # select ids matching for the specified  external_id
        ids = []
        custom_module_forms = response.get("customModuleForms", [])
        for form in custom_module_forms:
            if form.get("external_id") == external_id:
                ids.append(form.get("id"))

        return ids


    def get_form_by_id(
        self,
        form_id: str = None,
        ):
        """
        Reteive a specific form by its id
        See https://docs.gethealthie.com/docs/#retrieving-a-form

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
                        options
                        options_array       # The default options for this question, broken up into an array
                        position            # The position of the question (the lower the earlier the question is shown)
                        required            # Whether this question is required to be completed before the form it's in can be saved
                    }
                }
            }
        '''

        # Set up the variables for the GraphQL query
        variables = {'id': form_id}

        # Make the GraphQL query request using the send_query method inherited from HealthieAPI
        response = self.send_query(query, variables)

        return response



    def create_custom_module_form(
        self,
        name: str,
        use_for_charting: bool = False,
        use_for_program: bool = False,
        external_id: str = None,
        external_id_type: str = None,
        is_video: bool = False,
        on_completion_ifs_tag_id: str = None,
        prefill: bool = False
    ):
        """
        Create a CustomModuleForm using the Healthie API.
        See https://docs.gethealthie.com/docs/#creating-a-form

        Parameters:
            name (str): The name of the custom module form.
            use_for_charting (bool, optional): Indicates if the form is used for charting. Default False
            use_for_program (bool, optional): Indicates if the form is used for a program. Default False
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

        # Make the GraphQL mutation request using the send_query method inherited from HealthieAPI
        response = self.send_query(mutation, variables)
        return response

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
        # Set up the GraphQL mutation to create a CustomModule in a Form
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
                        external_id
                        label
                        mod_type
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

        # Make the GraphQL mutation request using the send_query method inherited from HealthieAPI
        response = self.send_query(mutation, variables)
        return response

    def create_custom_modules(
        self,
        custom_module_form_id: str,
        custom_modules: list
    ):
        """
        Create multiple CustomModules within a CustomModuleForm using the Healthie API.

        Parameters:
            custom_module_form_id (str): The ID of the CustomModuleForm to which the CustomModules will be added.
            custom_modules (list): A list of dictionaries, each representing a CustomModule to be created.
                                Each dictionary should contain at least 'label' and 'mod_type'.
                                Index have to start at 0 if form blank

        Returns:
            list: List of response data for each created CustomModule, containing IDs and messages.
        """
        # List to collect response data for each created CustomModule
        response_data_list = []

        i : int = 0
        # Iterate over each custom module dictionary
        for custom_module in custom_modules:
            # Extract parameters from the custom module dictionary
            label = custom_module['label']
            mod_type = custom_module['mod_type']
            # !!! index has to start at 0 if form blank
            # TODO : need to get number of modules if form not empty ?? Use the float variable ???
            index = custom_module.get('index', i) # use provided index or local iterator
            is_custom = custom_module.get('is_custom', False)
            external_id = custom_module.get('external_id', None)
            external_id_type = custom_module.get('external_id_type', None)
            options = custom_module.get('options', None)
            parent_custom_module_id = custom_module.get('parent_custom_module_id', None)
            required = custom_module.get('required', False)
            sublabel = custom_module.get('sublabel', None)

            # Create the custom module using the create_custom_module method
            response = self.create_custom_module(
                custom_module_form_id=custom_module_form_id,
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

            # Append response data to the list
            response_data_list.append(response)

            # increment index
            i = i + 1


        return response_data_list



    def create_form_wrapper(
        self,
        form_name: str,
        modules: list,
        use_for_charting: bool,
        use_for_program: bool,
        external_id: str = None,
        external_id_type: str = None,
        is_video: bool = False,
        on_completion_ifs_tag_id: str = None,
        prefill: bool = False,
    ):
        """
        Wrapper function to create a new form and its modules.

        Parameters:
            form_name (str): The name of the custom module form.
            use_for_charting (bool): Indicates if the form is used for charting.
            use_for_program (bool): Indicates if the form is used for a program.
            modules (list): A list of dictionaries, each representing a CustomModule to be created.
                            Each dictionary should contain at least 'label' and 'mod_type'.
            external_id (str, optional): External ID for relating form objects with third-party systems.
            external_id_type (str, optional): Type of external ID.
            is_video (bool, optional): Indicates if the form is a video module.
            on_completion_ifs_tag_id (str, optional): Tag ID for on-completion actions.
            prefill (bool, optional): Indicates if the form should be prefilled.

        Returns:
            dict: Response data containing the ID of the created custom module form and messages.
        """

        # Create the custom module form using the create_custom_module_form method
        form_response = self.create_custom_module_form(
            name=form_name,
            use_for_charting=use_for_charting,
            use_for_program=use_for_program,
            external_id=external_id,
            external_id_type=external_id_type,
            is_video=is_video,
            on_completion_ifs_tag_id=on_completion_ifs_tag_id,
            prefill=prefill,
        )

        # Extract the ID of the created custom module form
        custom_module_form_id = form_response['createCustomModuleForm']['customModuleForm']['id']

        # Create custom modules within the custom module form using the create_custom_modules method
        modules_responses = self.create_custom_modules(
            custom_module_form_id=custom_module_form_id,
            custom_modules=modules
        )

        # Check if there are any errors in the responses
        if 'errors' in form_response or 'errors' in modules_responses:
            raise Exception("Error creating form and modules.")

        # Return the modules_response
        return { "form_response" : form_response, "modules_responses" : modules_responses }


    # TODO : use our external_id to get answers ?
    def get_form_answers_group(
        self,
        custom_module_form_id: str = None,
        user_id: str = None,
        ):
        """
        Retreive form answer group. That is “A completed form, with metadata about the completion, and the saved answers”

        Parameters:
            custom_module_form_id (str): The ID of the CustomModuleForm
            user_id (str): The ID of the User

        Returns:
            dict:   Returns a formAnswerGroups object, with all FormAnswerGroup objects and FormAnswer
                    https://docs.gethealthie.com/schema/formanswergroup.doc
                    https://docs.gethealthie.com/schema/formanswer.doc

                answer:
                  - null if not completed
                  - '\n' separated if multichoice module
        """
        # Set up the GraphQL query to list custom module forms
        query = '''
            query formAnswerGroups(
                $custom_module_form_id: ID,
                $user_id: String,
            ) {
            formAnswerGroups(
                    custom_module_form_id: $custom_module_form_id,
                    user_id: $user_id,
                ) {
                    id
                    name
                    created_at
                    user_id                 # returns a Str
                    filler {                # The user who filled out the form. Returns a 'User' object https://docs.gethealthie.com/schema/user.doc
                        id
                    }
                    finished                # Whether the filled form has been saved by the user (versus a hidden draft)
                    locked_at               # The date and time when the charting note was locked
                    locked_by {             # The provider who have locked the charting note. Returns a 'User' object https://docs.gethealthie.com/schema/user.doc
                        id
                    }
                    custom_module_form {    # The form template that was filled out
                        id
                        name
                        external_id
                        use_for_charting
                        use_for_program
                    }
                    form_answers {
                        custom_module_id
                        label
                        answer
                        id
                    }
                }
            }
        '''

        # Set up the variables for the GraphQL query
        variables = {
            'custom_module_form_id': custom_module_form_id,
            'user_id' : user_id
            }

        # Make the GraphQL query request using the send_query method inherited from HealthieAPI
        response = self.send_query(query, variables)

        return response

    def get_form_answers_group_and_modules(
        self,
        custom_module_form_id: str = None,
        user_id: str = None,
        ):
        """
        Retreive form answer group. That is “A completed form, with metadata about the completion, and the saved answers”

        Parameters:
            custom_module_form_id (str): The ID of the CustomModuleForm
            user_id (str): The ID of the User

        Returns:
            dict:   Returns a formAnswerGroups object, with all FormAnswerGroup objects and FormAnswer with CustomModule
                    https://docs.gethealthie.com/schema/formanswergroup.doc
                    https://docs.gethealthie.com/schema/formanswer.doc
                    https://docs.gethealthie.com/schema/custommodule.doc

                answer:
                  - null if not completed
                  - '\n' separated if multichoice module
        """
        # Set up the GraphQL query to list custom module forms
        query = '''
            query formAnswerGroups(
                $custom_module_form_id: ID,
                $user_id: String,
            ) {
            formAnswerGroups(
                    custom_module_form_id: $custom_module_form_id,
                    user_id: $user_id,
                ) {
                    id
                    name
                    created_at
                    user_id                 # returns a Str
                    filler {                # The user who filled out the form. Returns a 'User' object https://docs.gethealthie.com/schema/user.doc
                        id
                    }
                    finished                # Whether the filled form has been saved by the user (verse a hidden draft)
                    locked_at               # The date and time when the charting note was locked
                    locked_by {             # The provider who have locked the charting note. Returns a 'User' object https://docs.gethealthie.com/schema/user.doc
                        id
                    }
                    custom_module_form {    # The form template that was filled out
                        id
                        name
                        external_id
                        use_for_charting
                        use_for_program
                    }
                    form_answers {
                        custom_module_id
                        custom_module {
                            id
                            external_id         # Custom column used by API users. Used to relate our form objects with objects in third-party systems
                            external_id_type    # Custom column used by API users. Used to relate our form objects with objects in third-party systems
                            label               # The label of the question
                            sublabel            # The sublabel (description) of the question
                            is_custom           # Whether this module is a custom module
                            mod_type            # The type of question
                            options
                            options_array       # The default options for this question, broken up into an array
                            position            # The position of the question (the lower the earlier the question is shown)
                            required            # Whether this question is required to be completed before the form it's in can be saved
                        }
                        label
                        answer
                        id
                    }
                }
            }
        '''

        # Set up the variables for the GraphQL query
        variables = {
            'custom_module_form_id': custom_module_form_id,
            'user_id' : user_id
            }

        # Make the GraphQL query request using the send_query method inherited from HealthieAPI
        response = self.send_query(query, variables)

        return response

    def get_form_answers_group_status(
        self,
        custom_module_form_id: str = None,
        user_id: str = None,
        ):
        """
        Retreive form answer group. That is “A completed form, with metadata about the completion”

        Parameters:
            custom_module_form_id (str): The ID of the CustomModuleForm
            user_id (str): The ID of the User

        Returns:
            dict:   Returns a formAnswerGroups object, with all FormAnswerGroup objects and FormAnswer
                    https://docs.gethealthie.com/schema/formanswergroup.doc
        """
        # Set up the GraphQL query to list custom module forms
        query = '''
            query formAnswerGroups(
                $custom_module_form_id: ID,
                $user_id: String,
            ) {
            formAnswerGroups(
                    custom_module_form_id: $custom_module_form_id,
                    user_id: $user_id,
                ) {
                    id
                    name
                    created_at
                    user_id                 # returns a Str
                    filler {                # The user who filled out the form. Returns a 'User' object https://docs.gethealthie.com/schema/user.doc
                        id
                    }
                    finished                # Whether the filled form has been saved by the user (verse a hidden draft)
                    locked_at               # The date and time when the charting note was locked
                    locked_by {             # The provider who have locked the charting note. Returns a 'User' object https://docs.gethealthie.com/schema/user.doc
                        id
                    }
                    custom_module_form {    # The form template that was filled out
                        id
                        name
                        external_id
                        use_for_charting
                        use_for_program
                    }
                }
            }
        '''

        # Set up the variables for the GraphQL query
        variables = {
            'custom_module_form_id': custom_module_form_id,
            'user_id' : user_id
            }

        # Make the GraphQL query request using the send_query method inherited from HealthieAPI
        response = self.send_query(query, variables)

        return response

    def find_mod_type_by_id(self, custom_modules, desired_id):
        for module in custom_modules:
            if module['id'] == desired_id:
                return module['mod_type']
        return None

    def get_modules_with_missing_answers(
        self,
        custom_module_form_id : str = None,
        user_id: str = None,
        ):
        """
          - Looks for null or unknown answers in a FormAnswerGroup
          - gets custom modules from these missing answers

          Can be used to report the number of questions with missing information

        Parameters:
            custom_module_form_id (str): The ID of the CustomModuleForm where to look for answers
            user_id (str): The ID of the User who answered the form

        Returns:
            dict: list of custom modules with missing answers
        """

        # Get form structure and modules
        custom_module_form = self.get_form_by_id(form_id=custom_module_form_id)

        # Extract customModuleForm and its custom_modules
        if 'customModuleForm' in custom_module_form:
            custom_modules = custom_module_form['customModuleForm'].get('custom_modules', [])
        else:
            custom_modules = []

        # Get answers
        answers = self.get_form_answers_group(
            custom_module_form_id=custom_module_form_id,
            user_id=user_id
            )

        # Extract custom_module_id where answer is missing
        """
        custom_module_ids_with_missing_answer = [
            fa["custom_module_id"]
            for group in answers["formAnswerGroups"]
                for fa in group["form_answers"]
                    if ( fa["answer"] is None and self.find_mod_type_by_id(custom_modules, fa['custom_module_id']) not in ['label'] )
                        or ( fa["answer"] in ['unknown', 'not available'] )
                        or ( fa["answer"] == "" and self.find_mod_type_by_id(custom_modules, fa['custom_module_id']) in ['text', 'textarea', 'number'] )
        ]
        """

        # Extract custom_module_id where answer is missing
        custom_module_ids_with_missing_answer = []

        for group in answers["formAnswerGroups"]:
            for fa in group["form_answers"]:
                answer = fa["answer"]
                custom_module_id = fa["custom_module_id"]
                mod_type = self.find_mod_type_by_id(custom_modules, custom_module_id)

                # Check conditions for missing answers
                if (answer is None and mod_type not in ['label']) \
                    or (answer in ['unknown', 'not available']) \
                        or (answer == "" and mod_type in ['text', 'textarea', 'number']):
                    custom_module_ids_with_missing_answer.append(custom_module_id)


        # Count missing answers per custom module
        custom_module_missing_answer_count = {}
        for custom_module_id in custom_module_ids_with_missing_answer:
            if custom_module_id in custom_module_missing_answer_count:
                custom_module_missing_answer_count[custom_module_id] += 1
            else:
                custom_module_missing_answer_count[custom_module_id] = 1

        # Build list of custom modules with missing answers and their counts
        custom_modules_with_missing_answer = []
        for custom_module in custom_modules:
            if custom_module['id'] in custom_module_ids_with_missing_answer:
                missing_answer_count = custom_module_missing_answer_count.get(custom_module['id'], 0)
                custom_modules_with_missing_answer.append({
                    'custom_module': custom_module,
                    'missing_answer_count': missing_answer_count
                })

        return custom_modules_with_missing_answer


    def build_form_from_gaps(
        self,
        custom_module_form_id : str,
        user_id: str,
        form_name: str,
        use_for_charting: bool,
        use_for_program: bool = False,
        external_id: str = None,
        external_id_type: str = None,
        is_video: bool = False,
        on_completion_ifs_tag_id: str = None,
        prefill: bool = False,
        ):
        """
          - Looks for null answers in a FormAnswerGroup
          - gets custom modules from these null answers
          - build a form with these custom modules

        Parameters:
            custom_module_form_id (str): The ID of the CustomModuleForm where to look for answers
            user_id (str): The ID of the User who answered the form

        Returns:
            dict: Response data containing the ID of the created custom module form and messages.
        """

        # Get form structure and modules
        custom_module_form = self.get_form_by_id(form_id=custom_module_form_id)

        # get modules of the form with a missing or unknown answer
        custom_modules_with_missing_answer = self.get_modules_with_missing_answers(
            custom_module_form_id=custom_module_form_id,
            user_id=user_id
        )

        new_form = self.create_form_wrapper(
            form_name=form_name,
            modules=custom_modules_with_missing_answer,
            use_for_charting=use_for_charting,
            use_for_program=use_for_program,
            external_id=external_id,
            external_id_type=external_id_type,
            is_video=is_video,
            on_completion_ifs_tag_id=on_completion_ifs_tag_id,
            prefill=prefill,
        )

        return new_form


    def create_form_completion_request(
        self,
        recipient_ids: str = "",
        form: str = "",
        is_recurring: bool = False,
        frequency: str = None,
        period: str = None,
        minute: str = None,
        hour: str = None,
        weekday: str = None,
        monthday: str = None,
        recurrence_ends: bool = None,
        ends_on: str = None,
    ):
        """
        Create a Form Completion Request using the Healthie API.
            See : - https://docs.gethealthie.com/docs/#creating-a-form-completion-request
                  - input : https://docs.gethealthie.com/schema/createrequestedforminput.doc
                  - createRequestedFormCompletion in https://docs.gethealthie.com/schema/mutation.doc

        Parameters:
            recipient_ids (str): A comma-separated list of user IDs and/or user group IDs.
            form (str):
            is_recurring (bool, optional):
            frequency (str, optional):
            period (str, optional):
            minute (str, optional):
            hour (str, optional):
            weekday (str, optional):
            monthday (str, optional):
            recurrence_ends (bool, optional):
            ends_on (str, optional):

        Returns:
            dict: Returns createRequestedFormPayload.
        """
        # Set up the GraphQL mutation to create a CustomModule in a Form
        mutation = '''
            mutation createRequestedFormCompletion(
                $recipient_ids: String,
                $form: String,
                $is_recurring: Boolean,
                $frequency: String,
                $period: String,
                $minute: String,
                $hour: String,
                $weekday: String,
                $monthday: String,
                $recurrence_ends: Boolean,
                $ends_on: String
            ) {
            createRequestedFormCompletion(input: {
                recipient_ids: $recipient_ids,
                form: $form,
                is_recurring: $is_recurring,
                frequency: $frequency,
                period: $period,
                minute: $minute,
                hour: $hour,
                weekday: $weekday,
                monthday: $monthday,
                recurrence_ends: $recurrence_ends,
                ends_on: $ends_on
            }) {
                requestedFormCompletion {
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
            'recipient_ids': recipient_ids,
            'form': form,
            'is_recurring': is_recurring,
            'frequency': frequency,
            'period': period,
            'minute': minute,
            'hour': hour,
            'weekday': weekday,
            'monthday': monthday,
            'recurrence_ends': recurrence_ends,
            'ends_on': ends_on,
        }

        # Make the GraphQL mutation request using the send_query method inherited from HealthieAPI
        response = self.send_query(mutation, variables)
        return response

    def list_completion_requests(
        self,
        user_id: str = None,
        status: str = None,
        keywords: str = None,
        ):
        """
        Retreive a list of completion requests sent to a user
        See https://docs.gethealthie.com/docs/#form-completion-request-object

        Parameters:
            user_id (str, Optional): The user id
            status (str, Optional): Can be either Open or Incomplete
            keywords (str, Optional): A term to search Requests by. Can be searched by Form Template name.

        Returns:
            dict:   Returns an array of RequestedFormCompletion objects.
                    See : https://docs.gethealthie.com/schema/requestedformcompletion.doc

        """
        # Set up the GraphQL query
        query = '''
            query requestedFormCompletions(
            $userId: ID,
            $keywords: String,
            $status: String
            ) {
            requestedFormCompletions(
                user_id: $userId,
                keywords: $keywords,
                status: $status
            ) {
                id                      # The unique identifier of the request
                custom_module_form_id   # The ID of the form to fill out
                date_to_show
            }
            }
        '''

        # Set up the variables for the GraphQL query
        variables = {
            'user_id': user_id,
            'keywords': keywords,
            'status': status,
            }

        # Make the GraphQL query request using the send_query method inherited from HealthieAPI
        response = self.send_query(query, variables)

        return response

    def was_form_completion_requested(
        self,
        user_id: str = None,
        form_id: str = None,
        ):
        """
        Looks whether a user was asked to complete a form, and when

        Parameters:
            user_id (str, Required): The user id
            form_id (str, Required): The form id

        Returns:
            set :  boolean, date of request

        """

        requests = self.list_completion_requests(user_id=user_id)

         # Initialize variables to store result
        form_requested = False
        request_date = None

        # Iterate through the list of completion requests
        for request in requests['requestedFormCompletions']:
            # Check if the form ID in the request matches the specified form ID
            if request['custom_module_form_id'] == form_id:
                # Set the result variables
                form_requested = True
                request_date = request['date_to_show']
                # No need to continue searching if a match is found
                break

        # Return the result
        return form_requested, request_date




if __name__ == "__main__":
    # Example usage of the list_forms function
    dotenv_path = ".env.staging"
    forms_api = HealthieAPIForms(dotenv_path=dotenv_path)

    if True:
        # List all forms
        response = forms_api.list_forms(sort_by='name_asc' , keywords='onboarding')
        print('==== All forms ====')
        print(json.dumps(response, indent=4))

        # Access the first ID in the customModuleForms array
        first_id = response['customModuleForms'][0]['id']

        if False:
            # Retrieve the first form
            print(f"\n==== Details of Form {first_id} and all its custom modules  ====")
            response = forms_api.get_form_by_id(first_id)
            print(json.dumps(response, indent=4))

        if False:
            # Retrieve the first form values
            print(f"\n==== Answer groups of Form {first_id} ====")
            response = forms_api.get_form_answers_group(custom_module_form_id=first_id)
            print(json.dumps(response, indent=4))

    if True:
        # get_modules_with_missing_answers
        print(f"\n==== get_modules_with_missing_answers ====")
        response = forms_api.get_modules_with_missing_answers(
            custom_module_form_id="1164773", user_id="1035117",
            )
        print(json.dumps(response, indent=4))

    if False:
        # build form from gaps
        print(f"\n==== build form from gaps ====")
        response = forms_api.build_form_from_gaps(
            custom_module_form_id="1162956", user_id="1035117",
            form_name='testing gaps',
            use_for_charting=False,
            use_for_program=False,
            )
        print(json.dumps(response, indent=4))

    if False:
        print(f"\n==== get form by external_id ====")
        response = forms_api.get_form_id_by_external_id(external_id='onboarding')
        print(json.dumps(response, indent=4))



