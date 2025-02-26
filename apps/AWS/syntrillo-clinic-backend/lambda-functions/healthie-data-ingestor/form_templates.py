from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.system.logger import logger

from healthie_api import run_graphql_query
from helpers import clean_text
from models import FormTemplate


def process_form_templates() -> None:
    """
    3 steps:
        1. Ingest from Healthie's Form Template GraphQL API (https://docs.gethealthie.com/docs/#form-templates)
        2. Flatten data json data returned from Healthie into a list of FormTemplates
        3. Push list of FormTemplates into our Amazon RDS (table: healthie_form_templates)

    Args:
        None
    Returns:
        None
    """
    graphql_output = fetch_all_form_templates_from_healthie()
    flattened_output = flatten_form_templates(graphql_output)
    insert_all_form_templates_to_sql(flattened_output)


def fetch_all_form_templates_from_healthie() -> dict:
    """
    Runs GraphQL query against Healthie's backend to fetch ALL the form templates.

    Args:
        None
    Returns:
        dict: The JSON response 'data' from the API.
    """
    graphql_query = '''
        query formTemplates(
            $include_default_templates: Boolean
            $active_status: Boolean
            $should_paginate: Boolean
            $category: String
            $keywords: String
            $offset: Int
            $sortBy: String
        ) {
            customModuleForms(
                include_default_templates: $include_default_templates
                active_status: $active_status
                should_paginate: $should_paginate
                category: $category
                keywords: $keywords
                offset: $offset
                sort_by: $sortBy
            ) {
                id
                name
                prefill
                uploaded_by_healthie_team
                custom_modules {
                id
                mod_type
                options
                label
                }
            }
        }
    '''
    # Query output is dict with a single key called "customModuleForms"
    # For example:
    # {
    #   "customModuleForms": [
    #         {
    #             "id": "2055450",
    #             "name": "Pau1",
    #             "prefill": false,
    #             "uploaded_by_healthie_team": false,
    #             "custom_modules": [
    #                 {
    #                     "id": "17612802",
    #                     "mod_type": "label",
    #                     "options": "",
    #                     "label": "Title"
    #                 },
    #                 {
    #                     "id": "17612803",
    #                     "mod_type": "radio",
    #                     "options": "a\nb\nc",
    #                     "label": "My question?"
    #                 }
    #             ]
    #         }
    #     ]
    # }

    logger.info("Fetching form templates from Healthie")
    try:
        output: dict = run_graphql_query(graphql_query)
        logger.info("Successfully fetched form templates")
        return output
    except Exception as e:
        logger.error(f"Error fetching form templates from Healthie: {e}")



def flatten_form_templates(json_data: dict) -> list[FormTemplate]:
    """
    Flattens the given `json_data` into a list of FormTemplates

    Args:
        json_data (dict): the json data returned from the Healthie's GraphQL API
    Returns:
        list[FormResponse]
    """

    flattened_templates = []

    # Extract the custom module forms from the JSON
    custom_module_forms = json_data.get("customModuleForms", [])

    if not custom_module_forms:
        logger.warning("No custom module forms found in the API response")
        return []

    # Iterate through each form
    for form in custom_module_forms:
        form_id = form.get("id", None)
        form_name = form.get("name", None)

        # Process each module within the form
        custom_modules = form.get("custom_modules", [])
        for module in custom_modules:
            module_id = module.get("id", None)

            # Create FormTemplate object if we have all required fields
            if all([module_id, form_id]):
                template = FormTemplate(
                    form_id = form_id,
                    module_id = module_id,
                    form_name = form_name,
                    module_label = clean_text(module.get("label", None)),
                    module_options = clean_text(module.get("options", None))
                )
                flattened_templates.append(template)

    return flattened_templates



def insert_all_form_templates_to_sql(flattened_templates: list[FormTemplate]) -> None:
    """
    Saves the given list of FormTemplate to Amazon RDS

    Args:
        flattened_templates (list[FormTemplate]): the list of FormTemplate to be saved
    Returns:
        None: the function does not return anything
    Raises:
        Exception: any type of exception while saving the data
    """

    # TODO: we are reusing this object, which does too many things but helps us move fast
    # Use it when it speeds you up, but don't implement more methods in it
    # This object should allow us to run arbitrary SQL queries against our internal
    # operational Amazon RDS

    if not flattened_templates:
        logger.warning("No templates to insert into database")
        return

    db_manager = SyntrilloDatabaseManager(syntrillo_internal_key="NOT_USED")
    db_connection = db_manager.conn

    try:
        with db_connection.cursor() as cursor:
            sql_query = """
                INSERT INTO healthie_form_templates (
                    form_id,
                    module_id,
                    form_name,
                    module_label,
                    module_options
                )
                VALUES (
                    %s, %s, %s, %s, %s
                )
                ON DUPLICATE KEY UPDATE
                    form_name=VALUES(form_name),
                    module_label=VALUES(module_label),
                    module_options=VALUES(module_options);
            """

            # Convert FormTemplate objects to dictionaries
            template_records = [
                (
                    template.form_id,
                    template.module_id,
                    template.form_name,
                    template.module_label,
                    template.module_options
                )
                for template in flattened_templates
            ]

            # Execute a bulk query for all records. More performant than cursor.execute() in a loop.
            cursor.executemany(sql_query, template_records)
            db_connection.commit()

            logger.info(f"Database updated with {len(template_records)} form template entries")

    except Exception as e:
        logger.exception = {
            f"Database error while inserting form templates. Error: {str(e)}"
        }
        raise e
    finally:
        db_manager.close_connection()
        logger.info("Database connection closed")