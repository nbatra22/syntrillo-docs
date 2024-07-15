
import json
import random

from typing import Tuple

from syntrillo.api_healthie.documents import HealthieDocuments
from syntrillo.api_healthie.forms import HealthieForms
from syntrillo.data_structures.storage_manager import DataStructureStorageManager

class ChartingNotePrefillHandler:
    """
    The ChartingNotePrefillHandler class is used to handle the prefilling of charting notes.


    """

    def __init__(
        self,
        healthie_user_id: str,
        ) -> None:
        """
        Initialize the ChartingNotePrefillHandler.

        Args:
            healthie_user_id (str): The Healthie user ID.

        """

        self.healthie_user_id = healthie_user_id

        self.healthie_documents = HealthieDocuments()

        self.healthie_forms = HealthieForms()

        self.storage_manager = DataStructureStorageManager()


    def list_private_folders(
        self,
        ) -> Tuple[dict, str]:
        """
        List the private folders for the user using the Healthie API.

        Returns:
            Tuple[dict, str]: The response and log.

        """

        response, log = self.healthie_documents.list_folders(
            healthie_user_id=self.healthie_user_id,
            is_private_to_user=True
            )

        return response, log

    def list_private_documents_in_folder(
        self,
        folder_id: str
        ) -> Tuple[dict, str]:
        """
        List the private documents in the specified folder using the Healthie API.

        Args:
            folder_id (str): The folder ID.

        Returns:
            Tuple[dict, str]: The response and log.

        """

        response, log = self.healthie_documents.list_documents(
            healthie_user_id=self.healthie_user_id,
            is_private_to_user=True,
            folder_id=folder_id
            )

        return response, log

    def list_private_folders_and_documents(
        self,
        ) -> Tuple[dict, str]:
        """
        List the private folders for the user using the Healthie API.

        It returns the private folders and the documents in each folder.

        Returns:
            Tuple[dict, str]: The response and log.

        """

        overall_log = {
            'success': True,
            'message': 'Successfully listed private folders and documents',
            'errors': []
        }

        # reponse has this structure: {'folders': [{'id': '10687', 'name': 'discharge_documents'}]}
        response, log = self.healthie_documents.list_folders(
            healthie_user_id=self.healthie_user_id,
            is_private_to_user=True
            )

        if log.get('success') is False:
            overall_log['success'] = False
            overall_log['message'] = 'Error: Unable to list private folders and documents'
            overall_log['errors'].append(log)
            return [], overall_log

        folders_and_documents = []
        if response.get('folders'):
            for folder in response['folders']:
                folder_id = folder['id']
                documents, log = self.list_private_documents_in_folder(folder_id=folder_id)

                if log.get('success') is False:
                    overall_log['success'] = False
                    overall_log['message'] = 'Error: Unable to list private folders and documents'
                    overall_log['errors'].append(log)
                else:
                    folders_and_documents.append({
                        'folder': folder,
                        'documents': documents.get('documents', [])
                    })

        return folders_and_documents, overall_log

    def get_charting_notes(
        self
    ) -> Tuple[dict, str]:
        """
        Get the charting notes for the user using the Healthie API.

        Include only charting ntoes with an external_id.

        Returns:
            Tuple[dict, str]: The response and log. The response includes these fields:
                - healthie_customModuleForms_id
                - name
                - syntrillo_id
                - syntrillo_id_type

        """

        try:
            forms = self.healthie_forms.list_forms(
                category='charting',
            )

            charting_notes = []

            for form in forms['customModuleForms']:
                if form['external_id']:
                    charting_notes.append({
                        'healthie_customModuleForms_id': form['id'],
                        'name': form['name'],
                        'syntrillo_id': form['external_id'],
                        'syntrillo_id_type': form['external_id_type'],
                        'created_at': form['created_at'],
                    })

            log = {
                'success': True,
                'message': 'Successfully listed private folders and documents',
            }

            return charting_notes, log

        except Exception as e:
            log = {
                'success': False,
                'message': f'Error: Unable to get charting notes: {str(e)}',
            }

            return [], log


    def run_prefill_ai_agent(
        self,
        healthie_customModuleForms_id: str,
        private_folder_id: str,
        ) -> dict:
        """


        Returns
          - log: A dictionary with the following keys
            - 'success': True if the operation was successful, False otherwise.
            - 'message': A message describing the result of the operation.
        """

        # --------------------------------------------------------------------
        # get customModuleForm metadata, related data structure and  modules
        temp = self.healthie_forms.get_form_by_id(form_id=healthie_customModuleForms_id)
        if not temp.get('customModuleForm'):
            log['success'] = False
            log['message'] = 'Error: Unable to get customModuleForm'
            return log

        custom_module_form = temp['customModuleForm']

        # our name, used in the data_structures module
        syntrillo_structure_name = custom_module_form['external_id']

        # get the data structure to obtain LLM information
        data_structure, log = self.storage_manager.retrieve_structure(structure_name=syntrillo_structure_name)

        # healthie custom modules
        healthie_custom_modules = custom_module_form['custom_modules']

        # initiate form_answers with blank answers for the create_a_filled_out_form call
        form_answers_blank = []

        # --------------------------------------------------------------------
        # loop through the custom modules
        for custom_module in healthie_custom_modules:
            # processing only modules with external_id
            if not custom_module['external_id']:
                continue

            # get structure item related to the custom module
            # ( structure['items'] is a list of dictionaries with 'internal_name' matching 'external_id')
            structure_item = None
            for item in data_structure['items']:
                if item['internal_name'] == custom_module['external_id']:
                    structure_item = item
                    break   # found the structure item

            if not structure_item:
                log['success'] = False
                log['message'] = 'Error: Unable to get structure item'
                return log

            # ---
            # add information to form_answers_blank
            form_answers_blank.append({
                "custom_module_id": custom_module['id'],
                "user_id": self.healthie_user_id,
                "answer" :  None,
                "LLM_data": {
                    "structure_metadata": data_structure.get('metadata', {}),
                    "structure_item": structure_item,
                }
            })

        print(json.dumps(form_answers_blank, indent=4, default=str))

        # --------------------------------------------------------------------
        # AI call
        dummy_ai_call = True

        if dummy_ai_call:
            form_answers_filled_out = []
            for form_answer in form_answers_blank:
                if form_answer.get('LLM_data').get('structure_item').get('display') == 'number':
                    data_point = str(random.randint(1, 100))
                else:
                    data_point = 'dummy answer'
                form_answers_filled_out.append({
                    "custom_module_id": form_answer['custom_module_id'],
                    "user_id": form_answer['user_id'],
                    "answer" : data_point,
                })

        # --------------------------------------------------------------------
        # create the filled out form for the patient
        form_answer_group_id, log1 = self.healthie_forms.create_a_filled_out_form(
            user_id=self.healthie_user_id,
            custom_module_form_id=healthie_customModuleForms_id,
            form_answers=form_answers_filled_out,
            finished=True,
        )

        if log1.get('success') is False:
            log = {
                'success': False,
                'message': 'Error: Unable to create a filled out form',
                'log1': log1,
            }
            return log


        log = {
            'success': True,
            'message': 'Successfully prefilling charting note',
            'form_answer_group_id': form_answer_group_id,
        }

        return log


if __name__ == '__main__':

    # Example usage
    # TODO : use syntrillo_internal_key to get the healthie_user_id
    healthie_user_id = '1035117'
    charting_note_prefill_handler = ChartingNotePrefillHandler(healthie_user_id=healthie_user_id)

    # List private folders
    response, log = charting_note_prefill_handler.list_private_folders()
    print(response)

    # List private documents in a folder
    folder_id = '10687'
    response, log = charting_note_prefill_handler.list_private_documents_in_folder(folder_id=folder_id)
    print(response)

    # List private folders and documents
    response, log = charting_note_prefill_handler.list_private_folders_and_documents()
    print(json.dumps(response, indent=4, default=str))
    print(log)
