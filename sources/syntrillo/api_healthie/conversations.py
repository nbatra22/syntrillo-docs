# Path: ./sources/syntrillo/api_healthie/conversations.py
import json
import os

from typing import Tuple

from syntrillo.system.logger import logger
from syntrillo.api_healthie.auth import HealthieAuth
from syntrillo.api_healthie.user import HealthieUser
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets


class HealthieConversations:
    """
    Retreives and manipulates Healthie Conversation and its Notes.

    https://docs.gethealthie.com/docs/#chat

    https://help.gethealthie.com/article/82-overview-chatting-with-a-client

    Within the API, a "Chat" is known as a Conversation. A message in a conversation is a Note object.


    """


    def __init__(
        self,
        ):
        """
        Initialize the HealthieConversations class.
        """
        self.auth = HealthieAuth()


    def get_conversation_id_from_note_id(
        self,
        note_id : str = None,
    ) -> Tuple[str, dict]:
        """
        Retreive the conversation id from a note id

        Args:
            note_id (str): The note id.

        Returns:
            conversation_id,log (Tuple[str, dict]): The conversation id and the log of the request

        """

        # get conversation id from note id
        response, log = self.auth.send_query(
            query="""
                query note($id: ID) {
                    note(id: $id) {
                        conversation_id
                    }
                }
                """,
            variables={'id': note_id}
        )

        if log['success'] and response is not None and response['note'] is not None:
            return response['note']['conversation_id'] , log
        else:
            return None, log


    def get_note_by_id(
        self,
        note_id : str = None,
    ) -> Tuple[dict, dict]:
        """
        Get full note details from its id

        https://docs.gethealthie.com/schema/note.doc

        Args:
            note_id (str): The note id.

        Returns:
           note,log (Tuple[dict, dict]): The note details and the log of the request

        """

        # get note from its id
        response, log = self.auth.send_query(
            query="""
                query note($id: ID) {
                    note(id: $id) {
                        content
                        conversation_id
                        created_at
                        creator {
                            id
                            name
                        }
                        document_id
                        document_name
                        updated_at
                        user_id             # creator of note
                    }
                }
                """,
            variables={'id': note_id}
        )

        if log['success'] and response is not None and response['note'] is not None:
            return response['note'], log
        else:
            return None, log


    def get_conversation_by_id(
    self,
    conversation_id : str = None,
    ) -> Tuple[dict, dict]:
        """
        Retreive the conversation details, including all notes content from its id

        Args:
            conversation_id (str): The conversation id.

        Returns:
            conversation,log (Tuple[dict, dict]): The conversation details and the log of the request

        """
        response, log = self.auth.send_query(
            query="""
                query getConversation($id: ID) {
                    conversation(id: $id) {
                        id
                        name
                        owner {
                            id
                            name
                        }
                        conversation_memberships_count
                        conversation_memberships {
                            id
                            user_id
                            conversation_role
                        }
                        includes_multiple_clients
                        invitees {
                            id
                        }
                        patient_id
                        notes {
                            id
                            content
                            user_id
                            created_at
                            creator {
                                id
                                is_patient
                            }
                        }
                    }
                }
                """,
            variables={'id': conversation_id}
        )

        if log['success'] and response is not None and response['conversation'] is not None:
            return response['conversation'], log
        else:
            return None, log


    def create_note(
        self,
        conversation_id : str = None,
        content : str = None,
        user_id : str = None,
    ):
        """
        add a new note in a conversation
        See : https://docs.gethealthie.com/docs/#createconversation-mutation

        Args:
            conversation_id (str): The conversation id.
            content (str): The content of the note.
            user_id (str): The user id of the creator of the note.

        Returns:
            messages,log (Tuple[dict, dict]): The messages and the log of the request

        """

        # get conversation id from note id
        response, log = self.auth.send_query(
            query="""
                    mutation createNote(
                    $user_id: String
                    $content: String
                    $conversation_id: String
                    $attached_image_string: String
                    $scheduled_at: String
                    $org_chat: Boolean
                    $hide_org_chat_confirmation: Boolean
                    ) {
                    createNote(
                        input: {
                        user_id: $user_id
                        content: $content                       # Content of the note
                        conversation_id: $conversation_id
                        attached_image_string: $attached_image_string
                        scheduled_at: $scheduled_at             # for scheduling notes, time note will be sent
                        org_chat: $org_chat                     # Pass `true` when creating a note by someone who is not the conversation owner (e.g., by another provider on the client's care team)
                        hide_org_chat_confirmation: $hide_org_chat_confirmation # When True, will hide org chat confirmation modal
                        }
                    ) {
                        note {
                            id
                            content
                            user_id
                        }
                        messages {
                            field
                            message
                        }
                    }
                }
                """,
            variables={
                'conversation_id': conversation_id,
                'content' : content,
                'user_id': user_id,
                }
        )

        return response, log

    def create_conversation(
        self,
        owner_id : str = None,
        members_ids : list = None,
        members_csv : str = None,
        name : str = None,
        ) -> Tuple[dict, dict]:
        """
        Create a new conversation.

        https://docs.gethealthie.com/docs/#creating-a-conversation

        Provide either members_ids or members_csv

        Args:
            owner_id (str): The owner id.
            members_ids (list): The list of members ids.
            members_csv (str): The list of members name as a csv string.
            name (str): The name of the conversation.

        Returns:
            conversation_id,log (Tuple[dict, dict]): The conversation id and the log of the request

        """

        #

        log = {
            'success': True,
            'message': 'create_conversation',
            'errors': []
        }

        # get members as comma separated doc_share_id values
        if members_ids is not None:
            members_csv = ''
            for member_id in members_ids:
                # get user name
                user = HealthieUser(healthie_user_id=member_id)
                doc_share_id = user.get_patient_information().get('doc_share_id', None)
                if doc_share_id is not None:
                    members_csv += f'{doc_share_id},'
                else:
                    log['errors'].append(f'User {member_id} does not have a doc_share_id')
                    log['success'] = False



        if members_csv is None or members_csv == '':
            log['errors'].append('No members in the conversation')
            log['success'] = False

        if log['success'] is False:
            return None, log

        # remove last comma
        if members_csv[-1] == ',':
            members_csv = members_csv[:-1]

        # create conversation
        response, log = self.auth.send_query(
            query="""
                mutation createConversation(
                    $owner_id: ID
                    $simple_added_users: String
                    $name: String
                ) {
                    createConversation(
                        input: {
                            owner_id: $owner_id
                            simple_added_users: $simple_added_users
                            name: $name
                        }
                    ) {
                        conversation {
                            id
                        }
                        messages {
                            field
                            message
                        }
                    }
                }
                """,
            variables={
                'owner_id': owner_id,
                'simple_added_users': members_csv,
                'name': name,
            }
        )

        return response, log

    def notify_clinicians(self, syntrillo_internal_key: str, systolic_bp: float, diastolic_bp: float, timestamp: str) -> None:
        """
        Notify clinicians when extreme blood pressure is detected

        Args:
            syntrillo_internal_key (str): Syntrillo internal key
            systolic_bp (float): Systolic blood pressure
            diastolic_bp (float): Diastolic blood pressure
            timestamp (str): Timestamp of the blood pressure measurement
        Returns:
            None
        """
        # Healthie Chat API Docs: https://docs.gethealthie.com/guides/chat/
        # Healthie Chat Overview: https://help.gethealthie.com/article/82-overview-chatting-with-a-client

        # 1. Create a new Healthie Conversation
        # Get patient name from the syntrillo_internal_key using the user_look_up_codes table
        patient_name, healthie_user_id = self.get_patient_name_from_syntrillo_internal_key(syntrillo_internal_key)

        # Retrieve healthie IDs env variable to use for conversation query
        secrets = LocalEnvironmentAndSecrets(load_healthie_secrets=True)
        healthie_ids = secrets.get_secrets(os.getenv("AWS_SECRETS_MANAGER_HEALTHIE_IDS_SECRET_ARN"))

        # Check if the environment is production or staging to determine which clinicians to notify
        # Get environment from SSM parameter store to determine which clinicians to notify
        env = get_aws_environment()
        if not env:
            logger.error("Environment variablenot found ...")
            return

        excluded_patients = healthie_ids.get(env, {}).get("EXCLUDED_PATIENTS", [])
        messenger_id = healthie_ids.get(env, {}).get("MESSENGER", "")
        clinicians = healthie_ids.get(env, {}).get("CLINICIANS", [])

        # If a specific patient is excluded from notifications, skip the notification
        if excluded_patients and healthie_user_id in excluded_patients:
            logger.info(f"Patient {patient_name} is excluded from notifications ...")
            return

        # The patient name is to be used as the title of the conversation
        # alert_title = f"⚠️ {patient_name} - BP Alert"
        alert_title = f"🔴 {patient_name} - BP Alert"

        # Check if the conversation already exists
        conversation_id = get_conversation_id(messenger_id, alert_title)
        if not conversation_id:
            # Create a new conversation
            conversation_output = make_conversation_query(clinicians, messenger_id, alert_title)
            conversation_id = conversation_output.get('createConversation', {}).get('conversation', {}).get('id')
            logger.info(f"Successfully created conversation in Healthie: {conversation_output}")


        # Add a note (aka a message) to the conversation
        response = add_note_to_conversation(messenger_id, conversation_id, systolic_bp, diastolic_bp, timestamp, syntrillo_internal_key)
        logger.info(f"Successfully added note to conversation in Healthie: {response}")


    def get_patient_name_from_syntrillo_internal_key(syntrillo_internal_key: str) -> tuple[str, str]:
        """
        Get patient name from the syntrillo_internal_key using the user_look_up_codes table
        Args:
            syntrillo_internal_key (str): The Syntrillo internal key
        Returns:
            tuple[str, str]: A tuple containing the patient name and healthie user id
        """

        # 1. Use syntrillo id to get healthie id
        db_manager = LookUpCodesManagement()
        entry = db_manager.retrieve_entry_by_internal_key(syntrillo_internal_key)
        healthie_user_id = entry.get('healthie_user_id', None)
        if not healthie_user_id:
            logger.error(f"Healthie user id not found for syntrillo_internal_key: {syntrillo_internal_key}")
            return

        # 2. Use healthie id to get patient name from Healthie API
        patient_name = get_healthie_user_information_by_healthie_user_id(healthie_user_id)
        if not patient_name:
            logger.error(f"Patient name not found for syntrillo_internal_key: {syntrillo_internal_key}")
            return
        return patient_name, healthie_user_id


    def get_healthie_user_information_by_healthie_user_id(healthie_user_id: str) -> str:
        """
        Get patient name from the healthie user id using the Healthie API
        Args:
            healthie_user_id (str): The ID of the healthie user
        Returns:
            str: The patient name
        """
        graphql_query = '''
            query getUser($id: ID) {
                user(id: $id) {
                id
                first_name
                last_name
                }
            }
        '''
        # Query output is dict with a single key called "data"
        # For example:
        # {
        #     "data": {
        #         "user": {
        #             "id": "2315391",
        #             "first_name": "Bob",
        #             "last_name": "Barker",
        #         }
        #     }
        # }
        logger.info("Adding note to conversation in Healthie...")
        try:
            variables = {
                "id": healthie_user_id
            }
            output: dict = HealthieUtils.run_graphql_query(graphql_query, variables)
            logger.info(f"Successfully retrieved user information from Healthie")

            first_name = output.get('user', {}).get('first_name', '')
            last_name = output.get('user', {}).get('last_name', '')
            return first_name + " " + last_name

        except Exception as e:
            logger.error(f"Error fetching user information from Healthie: {e}")




if __name__ == '__main__':

    # test create_conversation
    hc = HealthieConversations()
    owner_id = '1033222' # olivier+healthie_test2@15kay.fr
    members_ids = [
        '1664829', # Care Plan Personalization Virtual Assistant
        # '5f7c5c9c5e9d3f001b3f3b5d'
        ]
    name = 'test conversation'
    response, log = hc.create_conversation(owner_id=owner_id, members_ids=members_ids, name=name)
    print(json.dumps(response, indent=2))
    print(json.dumps(log, indent=2))
