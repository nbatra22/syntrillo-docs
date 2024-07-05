
import json
from typing import Tuple

from syntrillo.api_healthie.documents import HealthieDocuments
from syntrillo.api_healthie.forms import HealthieForms

class ChartingNotePrefillHandler:
    """



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

        Incluse only charting ntoes with an external_id.

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
    )-> dict:
        """
        """
        log = {
            'success': True,
            'message': 'Nothing there yet',
        }

        return log


if __name__ == '__main__':

    # Example usage
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
