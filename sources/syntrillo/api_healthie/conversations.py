import json

from typing import Tuple

from syntrillo.api_healthie.auth import HealthieAuth


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


