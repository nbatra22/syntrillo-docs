# modules/healthy/forms.py

import os
import sys
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from healthie.utils import HealthieAPIUtils
from healthie.misc import log_this

# the Virtual Care Navigator Healthie id (ie provider id)
VCN_ID : str ='1108460'

class HealthieAPIVirtualCareNavigator(HealthieAPIUtils):
    """
    A class extending HealthieAPIUtils to handle virtual care navigator operations.
    """

    def __init__(
        self,
        api_key: str = None,
        organization: str = 'staging',
        dotenv_path: str = None,
    ):
        super().__init__(api_key, organization, dotenv_path)


    def endpoint(
        self,
        data : dict  = None
    ) :
        """
            {"resource_id": 260040, "resource_id_type": "Note", "event_type": "message.created", "changed_fields": []}
        """

        # get whole conversation object
        note_id = data['resource_id']
        conversation = self.get_conversation_from_note_id(note_id=note_id)

        # test if owner if VCN account and if last message not from VCN (to prevent loops)
        owner_id = conversation['conversation']['owner']['id']

        # Get the last note in the list
        last_note = conversation['conversation']['notes'][-1]

        # Extract the user_id from the last note
        last_user_id = last_note['user_id']

        if owner_id == VCN_ID and last_user_id != VCN_ID:

            # get all the content of the conversation
            prompt = self.notes_to_prompt(notes=conversation['conversation']['notes'])

            # send new message
            response = self.create_note(
                conversation_id=conversation['conversation']['id'],
                content='blob',
                user_id=VCN_ID,
            )

        else:
            log_this(message=f"VCN: conversation owner not VCN: {owner_id}")
            response = None


        return response


    def get_conversation_from_note_id(
        self,
        note_id : str = None,
    ):
        """
        retreives the whole conversation from a note id:

        returns:
            dict : https://docs.gethealthie.com/schema/conversation.doc
        """

        # get conversation id from note id
        note = self.send_query(
            query="""
                query note($id: ID) {
                    note(id: $id) {
                        conversation_id
                    }
                }
                """,
            variables={'id': note_id}
        )
        conversation_id = note['note']['conversation_id']

        # get conversation from its id
        conversation = self.send_query(
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
                        includes_multiple_clients
                        invitees {
                            id
                        }
                        patient_id
                        notes {
                            content
                            user_id
                        }
                    }
                }
                """,
            variables={'id': conversation_id}
        )
        conversation_id = note['note']['conversation_id']

        return conversation

    def notes_to_prompt(
        self,
        notes : list = None,
    ):
        """
        stacks all contents of notes into a multiline text. Each content is separated from the next with a newline.

        Parameters:
            notes: list of healthie 'note' objects, with 'content' : https://docs.gethealthie.com/schema/note.doc

        Returns:
            str: Multiline text containing the contents of all notes separated by newline characters.

        """
        if notes is None:
            return ""  # Return an empty string if no notes are provided

        # Iterate over the list of notes and concatenate their contents with newline characters
        multiline_text = "\n".join(note["content"] for note in notes)

        return multiline_text

    def create_note(
        self,
        conversation_id : str = None,
        content : str = None,
        user_id : str = None,
    ):
        """
        add a new note in a conversation
        See : https://docs.gethealthie.com/docs/#createconversation-mutation

        """

        # get conversation id from note id
        response = self.send_query(
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
                        content: $content # Content of the note
                        conversation_id: $conversation_id
                        attached_image_string: $attached_image_string
                        scheduled_at: $scheduled_at # for scheduling notes, time note will be sent
                        org_chat: $org_chat # Pass `true` when creating a note by someone who is not the conversation owner (e.g., by another provider on the client's care team)
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

        return response



if __name__ == "__main__":
    # Example usage of the list_forms function
    dotenv_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/.env")
    vcn = HealthieAPIVirtualCareNavigator(dotenv_path=dotenv_path)

    if True:
        # test endpoint
        data = {"resource_id": 260046, "resource_id_type": "Note", "event_type": "message.created", "changed_fields": []}
        response = vcn.endpoint(data=data)

        print(json.dumps(response, indent=4))

