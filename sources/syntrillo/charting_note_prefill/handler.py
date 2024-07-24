
import json
import random
import pickle

import fitz  # TODO : pip install fitz? frontend? pymupdf ::: looks like 'import pymupdf' is enough
import io

from typing import Tuple

from syntrillo.api_healthie.documents import HealthieDocuments
from syntrillo.api_healthie.forms import HealthieForms
from syntrillo.data_structures.storage_manager import DataStructureStorageManager
from syntrillo.charting_note_prefill.jackson import ChartingNotePrefillJackson

class ChartingNotePrefillHandler:
    """
    The ChartingNotePrefillHandler class is used to handle the prefilling of charting notes with the  AI agent.

    Args:
        healthie_user_id (str): The Healthie user ID.

    """

    # class variables
    healthie_user_id: str = None
    healthie_documents: HealthieDocuments = None
    healthie_forms: HealthieForms = None
    storage_manager: DataStructureStorageManager = None

    def __init__(
        self,
        healthie_user_id: str,
        ) -> None:

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

        Include only charting notes with an external_id.

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

    def download_documents_content_from_folder(
        self,
        folder_id: str,
    ):
        """
        Download contents of all documents in a folder.

        Args:
           - folder_id (str): The folder ID.


        Returns a tuple with the following elements:
            - documents_with_binary_content (list): A list of dictionaries with the following keys
                - content (bytes): The binary content of the document.
                - file_name (str): The name of the file.
                - file_type (str): The type of the file.
            - log (dict): A dictionary with the following keys
                - 'success': True if the operation was successful, False otherwise.
                - 'message': A message describing the result of the operation.
                - 'list_private_documents_in_folder': The log of the list_private_documents_in_folder operation.
                - 'downloading_log': A list of logs for each document downloaded.

        """

        # initialize the log
        log = {
            "success": True
        }

        # --------------------------------------------------------------------
        # download all documents in the private folder
        # into a list of binary data
        documents, log1 = self.list_private_documents_in_folder(folder_id=folder_id)
        log['list_private_documents_in_folder'] = log1
        if log1.get('success') is False:
            log['message'] = 'Error: Unable to list private documents in folder'
            log['success'] = False
            return None, log

        # download the binary content of the documents
        documents_with_binary_content = []
        log['downloading_log'] = []
        for document in documents.get('documents', []):
            document_binary, log2 = self.healthie_documents.download_document(document_id=document['id'])
            log['downloading_log'].append(log2)
            if log2.get('success') is False:
                log['message'] = 'Error: Unable to download document'
                log['download_document'] = log2
                log['success'] = False
                return None, log
            # add the binary content to the list
            documents_with_binary_content.append({
                "content": document_binary,
                "file_name" : document['display_name'],
                "file_type": document['file_content_type'],
                })

        log['message'] = "All documents downloaded successfully"

        return documents_with_binary_content, log


    def run_prefill_ai_agent(
        self,
        healthie_customModuleForms_id: str,
        private_folder_id: str,
        ) -> dict:
        """
        Generate a filled out form for the patient using the AI agent.

        Args:
            - healthie_customModuleForms_id (str): The Healthie customModuleForms ID (ie our charting note template)
            - private_folder_id (str): The private folder ID, where the documents are stored in Healthie.

        Returns
          - log: A dictionary with the following keys
            - 'success': True if the operation was successful, False otherwise.
            - 'message': A message describing the result of the operation.
            - 'form_answer_group_id (str): The ID of the form answer group created, if successful.
        """

        # initialize the overall log
        overall_log = {
            'success': True,
            'message': '',
            'form_answer_group_id': None,
        }

        # --------------------------------------------------------------------
        # download all documents in the private folder
        # into a list of binary data
        documents_with_binary_content, log1 = self.download_documents_content_from_folder(folder_id=private_folder_id)

        if log1.get('success') is False:
            overall_log['message'] = 'Error: Unable to download document'
            overall_log['download_document'] = log1
            return overall_log

        overall_log['len_document_binary'] = len(documents_with_binary_content)

        if False:
            # Save documents_with_binary_content to a file
            with open('ignore_documents_with_binary_content.pkl', 'wb') as f:
                pickle.dump(documents_with_binary_content, f)

        # --------------------------------------------------------------------
        # get customModuleForm metadata, related data structure and  modules
        #  : custom_module_form is the Healthie representation of our Charting  Note
        #  : data_structure is the Syntrillo representation of the Charting Note
        temp = self.healthie_forms.get_form_by_id(form_id=healthie_customModuleForms_id)
        if not temp.get('customModuleForm'):
            overall_log['success'] = False
            overall_log['message'] = 'Error: Unable to get customModuleForm'
            return overall_log

        custom_module_form = temp['customModuleForm']

        # our name, used in the data_structures module
        syntrillo_structure_name = custom_module_form['external_id']

        # get the data structure to obtain LLM information
        data_structure, log3 = self.storage_manager.retrieve_structure(structure_name=syntrillo_structure_name)
        overall_log['retrieve_structure'] = log3
        if log3.get('success') is False:
            overall_log['success'] = False
            overall_log['message'] = 'Error: Unable to retrieve structure'
            return overall_log

        # healthie custom modules
        healthie_custom_modules = custom_module_form['custom_modules']

        # --------------------------------------------------------------------
        # create a form_answers_blank list
        #  : this list will be filled out by the AI agent
        #  : it will be used to create the filled out form
        #  : each element in the list is a dictionary with the following keys
        #    - custom_module_id
        #    - user_id
        #    - answer
        #    - LLM_data : information related to this item of the data structure


        # initiate form_answers with blank answers for the create_a_filled_out_form call
        form_answers_blank = []

        # loop through the custom modules to list the answers the AI agent will fill out
        for custom_module in healthie_custom_modules:
            # processing only modules with external_id
            if not custom_module['external_id']:
                continue

            # get structure item related to the custom module
            #  : structure['items'] is a list of dictionaries with 'internal_name' matching 'external_id'
            #    including version number
            structure_item = None
            for item in data_structure['items']:
                if item['internal_name'] == custom_module['external_id']:
                    structure_item = item
                    break   # found the structure item

            # if structure item is not found, log error and return
            if not structure_item:
                overall_log['success'] = False
                overall_log['message'] = 'Error: Unable to get structure item'
                return overall_log

            # ---
            # add information to form_answers_blank
            #  : TODO : we're adding the structure metadata everytime, but it's the same for all items
            #         : this can be optimized
            form_answers_blank.append({
                "custom_module_id": custom_module['id'],
                "user_id": self.healthie_user_id,
                "answer" :  None,
                "LLM_data": {
                    "structure_metadata": data_structure.get('metadata', {}),
                    "structure_item": structure_item,
                }
            })

        overall_log['form_answers_blank'] = form_answers_blank

        # --------------------------------------------------------------------
        # AI call
        """
        form_answers_filled_out = external_AI_call(
            form_answers_blank,
            documents_binary
        )
        """
        ai_call_type = 'jackson'

        if ai_call_type == 'jackson' :
            jackson = ChartingNotePrefillJackson()

            jackson.load_documents(documents_with_binary_content=documents_with_binary_content)

            form_answers_filled_out, log_jackson = jackson.fill_form_from_discharge(form_answers_blank=form_answers_blank)

            # log and return if error
            overall_log['jackson_log'] = log_jackson
            if log_jackson.get('success') is False:
                overall_log['success'] = False
                overall_log['message'] = 'Error: Unable to fill out form with Jackson AI'
                return overall_log

        else:
            # dummy AI call : fill out the form with random data
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
            overall_log['dummy_ai_call'] = {
                'success': True,
                'message': 'Successfully completed dummy AI call',
            }

        # log results
        overall_log['form_answers_filled_out'] = form_answers_filled_out

        # --------------------------------------------------------------------
        # create the filled out form for the patient

        # create a form_answers_filled_out_cleand from form_answers_filled_out, with only:
        #  - custom_module_id
        #  - user_id
        #  - answer
        form_answers_filled_out_clean = []
        for form_answer in form_answers_filled_out:
            form_answers_filled_out_clean.append({
                "custom_module_id": form_answer['custom_module_id'],
                "user_id": form_answer['user_id'],
                "answer" : form_answer['answer'],
            })

        # create the filled out form
        form_answer_group_id, log4 = self.healthie_forms.create_a_filled_out_form(
            user_id=self.healthie_user_id,
            custom_module_form_id=healthie_customModuleForms_id,
            form_answers=form_answers_filled_out_clean,
            finished=True,
        )
        overall_log['create_a_filled_out_form_log'] = log4

        if log4.get('success') is False:
            overall_log['success'] = False
            overall_log['message'] = 'Error: Unable to create a filled out form'
            return overall_log

        # --------------------------------------------------------------------
        # final log
        overall_log['success'] = True
        overall_log['message'] = 'Successfully prefilling charting note'
        overall_log['form_answer_group_id'] = form_answer_group_id

        return overall_log


if __name__ == '__main__':

    # Example usage
    # TODO : use syntrillo_internal_key to get the healthie_user_id
    healthie_user_id = '1035117'
    charting_note_prefill_handler = ChartingNotePrefillHandler(healthie_user_id=healthie_user_id)

    if False:
    # List private folders
        response, log = charting_note_prefill_handler.list_private_folders()
        print(response)

    if False:
    # List private documents in a folder
        folder_id = '10687'
        response, log = charting_note_prefill_handler.list_private_documents_in_folder(folder_id=folder_id)
        print(response)

    if False:
        # List private folders and documents
        response, log = charting_note_prefill_handler.list_private_folders_and_documents()
        print(json.dumps(response, indent=4, default=str))
        print(log)

    if False:
    # download content
        folder_id = '10687'
        documents_with_binary_content, log = charting_note_prefill_handler.download_documents_content_from_folder(folder_id=folder_id)
        print(log)

        # Save documents_with_binary_content to a file
        with open('ignore_documents_with_binary_content.pkl', 'wb') as f:
            pickle.dump(documents_with_binary_content, f)
            print('pickle saved')

    if True:
        # test PDF import

        # Load documents_binary from the file
        with open('ignore_documents_with_binary_content.pkl', 'rb') as f:
            documents_with_binary_content = pickle.load(f)

        # Process each binary document as if it was a file
        for document in documents_with_binary_content:
            # Use io.BytesIO to create a file-like object
            file_like_object = io.BytesIO(document.get('content'))

            # Use fitz to open the document from the file-like object
            doc = fitz.open(stream=file_like_object, filetype=document.get('file_type'))

            print('-----')
            print(document.get("file_name"))
            page = doc.load_page(1)
            text = page.get_text("text")
            lines = text.splitlines()
            print(lines[0])



