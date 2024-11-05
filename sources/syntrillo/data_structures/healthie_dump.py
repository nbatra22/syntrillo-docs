import pandas as pd
import json
import io

from typing import Tuple

from syntrillo.api_healthie.auth import HealthieAuth

class DataStructureHealthieDump:

    def __init__(self):
        self.auth = HealthieAuth()

        self.log = {
            'success': True,
            'message': []
        }

        self.response = None

        self.file_name = 'healthie_data_structure_dump'

        # excel options
        self.include_labels = False
        self.include_dates = False
        self.single_sheet = False
        self.include_external_ids = False


    def run_query(
        self,
        include_default_templates: bool = False,
        active_status: bool = False,
        should_paginate: bool = False,
        category: str = None,
        keywords: str = None,
        offset: int = 0,
        sort_by: str = 'name_asc',
    ) -> Tuple[dict, str]:
        """
        Run a query to retrieve data from Healthie.
        """

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
        response, log = self.auth.send_query(query, variables)

        self.response = response

        self.log['message'].append(log)
        self.log['success'] = self.log['success'] and log['success']


    def _get_row(
        self,
        form: dict,
        module: dict,
        ) -> dict:
            """
            Get a row of data from the form and module dictionaries.
            """
            row = {
                'form_id': form['id'],
                'form_name': form['name'],
            }
            if self.include_external_ids:
                row.update({
                'form_external_id': form['external_id'],
                'form_external_id_type': form['external_id_type'],
                })
            if self.include_dates:
                row.update({
                'created_at': form['created_at'],
                'updated_at': form['updated_at'],
                })
            row.update({
                'module_id': module['id'],
                'module_type': module['mod_type'],
            })
            if self.include_external_ids:
                row.update({
                'module_external_id': module['external_id'],
                'module_external_id_type': module['external_id_type'],
                })
            row.update({
                'module_label': module['label'],
                'module_sublabel': module['sublabel'],
                'options_array': module['options_array']
                })

            return row


    def convert_to_excel(
        self,
        ) -> io.BytesIO:

        if self.response is None:
            self.run_query()

        # get data
        data = self.response

        # get options
        single_sheet = self.single_sheet
        include_labels = self.include_labels

        if single_sheet:
            # Initialize lists to hold data for the DataFrame
            rows = []

            # Iterate over customModuleForms and extract relevant data
            for form in data['customModuleForms']:
                for module in form['custom_modules']:
                    row = self._get_row(form, module)
                    if not include_labels and module['mod_type'] in ['label', 'read_only']:
                        pass
                    else:
                        rows.append(row)

            # Create a DataFrame from the list of rows
            df = pd.DataFrame(rows)

            output = io.BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)  # Move cursor to the beginning of the BytesIO object

        else:
            # Initialize a dictionary to hold data for each sheet
            data_dict = {}

            # Iterate over customModuleForms and extract relevant data
            for form in data['customModuleForms']:
                rows = []
                for module in form['custom_modules']:
                    row = self._get_row(form, module)
                    if not include_labels and module['mod_type'] in ['label', 'read_only']:
                        pass
                    else:
                        rows.append(row)

                # Create a DataFrame from the list of rows
                df = pd.DataFrame(rows)
                data_dict[form['name']] = df

            # Create an Excel writer object
            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='openpyxl')

            # Write each DataFrame to a separate sheet in the Excel file
            for sheet_name, df in data_dict.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

            writer.close()
            output.seek(0)

        return output



    def get_data_dump(
        self,
        dump_data_type: str
        ) -> Tuple[bytes, str, str, dict]:
        """
        Generates a small dummy dataset and returns it in the requested format.

        Args:
            dump_data_type (str): The format of the dump ('json' or 'xlsx').

        Returns:
            tuple: A tuple containing the file bytes, the full name of the file,
                   the MIME type, and a log message.
        """

        if self.response is None:
            self.run_query()

        data = self.response


        # Depending on the requested type, return the corresponding format
        if dump_data_type == 'json':
            # Convert to JSON
            json_data = json.dumps(data, indent=4)

            # encode() is used to convert the string to bytes
            json_data_bytes = json_data.encode()

            log = {
                'success': True,
                'message': 'JSON data generated successfully.'
            }

            return (json_data_bytes , self.file_name + '.json', 'application/txt', log)

        elif dump_data_type == 'xlsx':
            output = self.convert_to_excel()
            output.seek(0)  # Move cursor to the beginning of the BytesIO object
            log = {
                'success': True,
                'message': 'XLSX data generated successfully.'
            }
            return (output.read(), self.file_name + '.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', log)

        else:
            log = {
                'success': False,
                'message': 'Unsupported dump_data_type.'
            }
            return (None, None, None, log)

# Example usage:
if __name__ == "__main__":
    manager = DataStructureHealthieDump()
    dump_data_type = 'xlsx'  # or 'xlsx'
    dump_bytes, full_name, mimetype, log = manager.retrieve_dump(dump_data_type)

    # Print results for demonstration
    print(f"Log: {log}")
    print(f"Filename: {full_name}, MIME type: {mimetype}")
    if dump_data_type == 'json':
        print(dump_bytes.decode('utf-8'))  # Print JSON content
    elif dump_data_type == 'xlsx':
        print(f"Generated {full_name} with {len(dump_bytes)} bytes.")
