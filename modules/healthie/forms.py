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

                    custom_modules { label } # "A question in a form template" : https://docs.gethealthie.com/schema/custommodule.doc

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


if __name__ == "__main__":
    # Example usage of the list_forms function
    dotenv_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/.env")
    forms_api = HealthieAPIForms(dotenv_path=dotenv_path)

    # tests
    try:
        # List all forms
        response = forms_api.list_forms(sort_by='name_asc', keywords='Scoring')
        print(json.dumps(response, indent=4))

    except ValueError as ve:
        print(f"ValueError: {ve}")
        exit()
