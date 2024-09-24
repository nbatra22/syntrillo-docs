# Path: ./sources/syntrillo/chatbots/conversation_wrapper.py
import json

from typing import Tuple
from datetime import datetime

from syntrillo.api_healthie.conversations import HealthieConversations
from syntrillo.api_healthie.user import HealthieUser

class ChatBotConversationWrapper:
    """
    Retreives and manipulates a Conversation and its Notes.


    """

    log = {
        'success': True,
        'logs': []
    }

    def __init__(self) -> None:
        """
        Initialize the VirtualCareNavigatorConversationWrapper class.
        """
        self.convo = HealthieConversations()

        # ------------------------------------------------
        # initialize variables
        self.note_id = None
        self.conversation_id = None

        self.note = None
        self.conversation = None

        # HealthieUser class
        self.owner = None

        # HealthieUser class array
        self.patients = None  # typically one patient
        self.members = None
        self.creators = None  # every note creator

        # all creators ids
        self.creators_ids = None


    def get_log(self) -> dict:
        """
        Get the log of the requests

        Returns:
            log (dict): The log of the request.
        """
        return self.log

    def load_conversation_from_note_id(self, note_id: str) -> dict:
        """
        Load the conversation from the note_id.

        Args:
            note_id (str): The note id.

        Returns:
            log (dict): The log of the request.
        """

        # ---
        # load note from note id
        self.note_id = note_id
        self.note, log = self.convo.get_note_by_id(note_id)
        if self.note is None or not log['success']:
            self.log['success'] = False
            self.log['logs'].append({
                'message' : 'Failed to get note',
                'note_id' : note_id,
                'log' : log
            })
            return self.log

        # ---
        # get conversation id from note id
        self.conversation_id, log = self.convo.get_conversation_id_from_note_id(note_id)

        if self.conversation_id is None or not log['success']:
            self.log['success'] = False
            self.log['logs'].append({
                'message' : 'Failed to get conversation id from note id',
                'note_id' : note_id,
                'log' : log
            })
            return self.log

        # ---
        # load whole conversation from conversation id
        log = self.load_conversation_from_conversation_id(self.conversation_id)
        if not log['success']:
            self.log['success'] = False
            self.log['logs'].append({
                'message' : 'Failed to get conversation from conversation id',
                'conversation_id' : self.conversation_id,
                'log' : log
            })
            return self.log



        return self.log

    def load_conversation_from_conversation_id(self, conversation_id: str) -> dict:
        """
        Load the conversation from the conversation_id.

        Args:
            conversation_id (str): The conversation id.

        Returns:
            log (dict): The log of the request.

        """
        self.conversation_id = conversation_id
        self.conversation, log = self.convo.get_conversation_by_id(conversation_id)

        if self.conversation is None or not log['success']:
            self.log['success'] = False
            self.log['logs'].append({
                'message' : 'Failed to get conversation',
                'conversation_id' : conversation_id,
                'log' : log
            })
            return self.log

        try:
            # get owner (always a provider)
            self.owner = HealthieUser(healthie_user_id=self.conversation['owner']['id'])

            # get invitees
            self.patients = []
            for member in self.conversation['invitees']:
                temp_user = HealthieUser(healthie_user_id=member['id'])
                if temp_user.is_patient():
                    self.patients.append(temp_user)

            # get conversation members
            self.members = []
            for member in self.conversation['conversation_memberships']:
                self.members.append(HealthieUser(healthie_user_id=member['user_id']))

            # get all unique creators from all the notes in the conversation
            self.creators = []
            self.creators_ids = []
            for note in self.conversation['notes']:
                creator = HealthieUser(healthie_user_id=note['creator']['id'])
                if creator.healthie_user_id not in self.creators_ids:
                    self.creators.append(creator)
                    self.creators_ids.append(creator.healthie_user_id)


        except Exception as e:
            self.log['success'] = False
            self.log['logs'].append({
                'message' : 'Failed to get conversation members',
                'conversation_id' : conversation_id,
                'log' : str(e)
            })

        return self.log

    def get_note(self) -> dict:
        """
        Get the note details.

        Returns:
            dict: The note details.
        """
        return self.note

    def get_note_content(self) -> str:
        """
        Get the note content.

        Returns:
            str: The note content.
        """
        return self.note['content']

    def get_note_creator(self) -> HealthieUser:
        """
        Get the creator of the note.

        Returns:
            HealthieUser: The creator of the note.
        """

        # TODO : check if the creator is a provider or a patient
        return HealthieUser(healthie_user_id=self.note['user_id'])

    def get_conversation(self) -> dict:
        """
        Get the conversation details.

        Returns:
            dict: The conversation details.
        """
        return self.conversation

    def get_conversation_owner(self) -> HealthieUser:
        """
        Get the owner id of the conversation (should be the provider).

        Returns:
            HealthieUser: The owner of the conversation.
        """
        return self.owner

    def get_patients(self) -> HealthieUser:
        """
        Get the patient of the conversation.

        Returns:
            patients list(HealthieUser): The patients in the conversation.
        """
        return self.patients

    def does_convo_includes_multiple_clients(self) -> bool:
        """
        Check if the conversation includes multiple clients.

        Should be a show stopper for the VCN

        Returns:
            bool: True if the conversation includes multiple clients, False otherwise.
        """
        return self.conversation['includes_multiple_clients']

    def list_convo_member_ids(self) -> list:
        """
        List the conversation members.

        Returns:
            list: The conversation members.
        """
        members = self.conversation['conversation_memberships']
        ids = []
        for member in members:
            ids.append(member['user_id'])

        return ids

    def get_all_convo_creators(self) -> list:
        """
        Get all the conversation note creators.

        Returns:
            creators (list[HealthieUser]): The conversation creators.
        """
        return self.creators

    def is_user_in_convo(self, healthie_user_id: str) -> bool:
        """
        Check if the user is in the conversation.

        Args:
            healthie_user_id (str): The user id.

        Returns:
            bool: True if the user is in the conversation, False otherwise.
        """
        return healthie_user_id in self.creators_ids


    def create_note(
        self,
        content: str,
        healthie_user_id: str
        ) -> Tuple[dict, dict]:
        """
        Create a note in the conversation.

        Args:
            content (str): The content of the note.
            healthie_user_id (str): The user id of the note creator.

        Returns:
            Tuple[dict, dict]: The note details and the log of the request.
        """
        message, log = self.convo.create_note(
            conversation_id=self.conversation_id,
            content=content,
            user_id=healthie_user_id
            )

        if message is None or not log['success']:
            self.log['success'] = False
            self.log['logs'].append({
                'message' : 'Failed to create note',
                'conversation_id' : self.conversation_id,
                'log' : log
            })

        return message, log

    def get_all_notes_for_llm(
        self,
        chatbot_user_id: str = None,
        keyword_to_remove_from_content: str = None
        ) -> Tuple[dict, dict]:
        """
        Returns all notes from the conversation as a list of dictionaries having the following format:
            {
                'who': 'patient', 'provider' or 'chatbot'
                'content': 'content',
                'created_at': 'created_at',
            }

        Args:
            chatbot_user_id (str): The chatbot user id.

        Returns:
            notes (list[dict]): The notes from the conversation.

        """
        notes = []
        for note in self.conversation['notes']:
            if note['creator']['is_patient']:
                who = 'patient'
            else:
                if chatbot_user_id is None:
                    who = 'provider or chatbot'
                else:
                    if note['user_id'] == chatbot_user_id:
                        who = 'chatbot'
                    else:
                        who = 'provider'

            # remove keyword from content
            if keyword_to_remove_from_content:
                content = note['content'].replace(keyword_to_remove_from_content, '')
            else:
                content = note['content']

            notes.append({
                'who': who,
                'content': content,
                'created_at': note['created_at']
            })

        return notes

    def get_all_notes_for_llm_as_openai_messages(
        self,
        chatbot_user_id: str = None,
        keyword_to_remove_from_content: str = None,
    ):
        """

        Returns a list of messages in the format of OpenAI messages:
        {
            "role": "user" or "assistant",
            "content": assistant_message or patient/provider_message as json { who , content, created_at }
        }

        """
        notes = self.get_all_notes_for_llm(chatbot_user_id, keyword_to_remove_from_content)
        messages = []
        for note in notes:
            if note['who'] == 'chatbot':
                role = "assistant"
                content = note['content']
            else:
                role = "user"
                content = json.dumps(note, default=str)
            messages.append({
                "role": role,
                "content": str(content)
            })

        return messages

    def get_last_note_datetime(self) -> datetime:
        """
        Get the datetime of the last note.

        Returns:
            datetime: The datetime of the last note (created_at).
        """

        # with this format : "2024-07-11 17:51:16 +0200"
        created_at = self.conversation['notes'][-1]['created_at']

        # convert created_at to datetime
        dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S %z')

        return dt




if __name__ == '__main__':

    # test ChatBotConversationWrapper from a conversation_id
    conversation_id = '1562883'
    wrapper = ChatBotConversationWrapper()
    log = wrapper.load_conversation_from_conversation_id(conversation_id)

    print(json.dumps(wrapper.get_conversation(), indent=4, default=str))

    print("owner is provider:" , wrapper.get_conversation_owner().is_provider())

    print('---------------')
    notes = wrapper.get_all_notes_for_llm(chatbot_user_id='1459460')
    print(json.dumps(notes, indent=4, default=str))

    print('---------------')
    # show all note creators
    creators = wrapper.get_all_convo_creators()
    for member in creators:
        print(member.healthie_user_id , member.get_patient_information()['name'])




