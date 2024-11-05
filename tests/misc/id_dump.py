# testing ID dump queries

import json
import html

from syntrillo.api_healthie.auth import HealthieAuth

def main():

    auth = HealthieAuth()

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
                name
                created_at
                external_id
                external_id_type
                updated_at
                use_for_charting
                use_for_program

                # "A question in a form template" : https://docs.gethealthie.com/schema/custommodule.doc
                custom_modules {
                    id
                    label
                    sublabel
                    external_id
                    external_id_type
                    mod_type
                    options
                    options_array
                }

            }
        }
    '''

    # Set up the variables for the GraphQL query

    include_default_templates: bool = False
    active_status: bool = False
    should_paginate: bool = False
    category: str = None
    keywords: str = None
    offset: int = 0
    sort_by: str = 'name_asc'

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
    response, log = auth.send_query(query, variables)

    # Print the response (pretty-printed)
    print("Response:")
    print(json.dumps(response, indent=4))

    # Print the log (pretty-printed)
    print("Log:")
    print(json.dumps(log, indent=4))



if __name__ == "__main__":
    # Call the main function
    main()
