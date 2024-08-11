import json

from typing import Tuple

from datetime import datetime
import pytz

from syntrillo.chatbots.conversation_wrapper import ChatBotConversationWrapper
from syntrillo.chatbots.after_hours_support import AfterHoursSupportChatBot
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.helper_functions.html import remove_html_tags

class ChatBotsDispatcher:
    """
    This class is responsible for dispatching messages to the appropriate chatbot.

    """

    def __init__(self):
        self.healthie_utils = HealthieUtils()
        self.convo_wrapper = None


    def endpoint(self, data: dict):
        """
        The endpoint for the chatbot dispatcher.

        Receives a data dict similar to:
            {"resource_id": 260040, "resource_id_type": "Note", "event_type": "message.created", "changed_fields": []}
        where
            data['resource_id_type'] == "Note"
            data['event_type'] == "message.created":
            resource_id is the note_id

        """

        # Get the note_id
        note_id = data['resource_id']

        # Load the conversation from the note_id
        self.convo_wrapper = ChatBotConversationWrapper()
        log = self.convo_wrapper.load_conversation_from_note_id(note_id)

        # ------------------------------
        # dispatch the message to the appropriate chatbot, based on time and several variables
        note_creator = self.convo_wrapper.get_note_creator()
        note_content = self.convo_wrapper.get_note_content()
        convo_includes_multiple_clients = self.convo_wrapper.does_convo_includes_multiple_clients()
        conversation_owner = self.convo_wrapper.get_conversation_owner()
        patients = self.convo_wrapper.get_patients()
        is_org_staging = self.healthie_utils.is_org_staging()

        # Remove HTML tags from note content
        note_content_clean = remove_html_tags(note_content)

        # chatbot to start or not
        start_after_hours_support_chatbot = False
        start_virtual_care_navigator_chatbot = False

        # Get the current time in the EST timezone
        est = pytz.timezone('US/Eastern')
        current_time_est = datetime.now(est)

        if is_org_staging:
            # We are in staging

            # Define the start and end time for the working hours (9 AM to 5 PM)
            start_time = current_time_est.replace(hour=9, minute=0, second=0, microsecond=0)
            end_time = current_time_est.replace(hour=17, minute=0, second=0, microsecond=0)
            is_within_working_hours = start_time <= current_time_est <= end_time

            if note_creator.is_provider():
                # if the note creator is a provider only start if content starts with a keyword
                if note_content_clean.startswith(AfterHoursSupportChatBot.MANUAL_KICK_START_TAG_KEYWORD):
                    start_after_hours_support_chatbot = True
                elif note_content_clean.startswith('@vcn'):
                    start_virtual_care_navigator_chatbot = True
            else:
                # if the note creator is a provider only start if content starts with a keyword
                if note_content_clean.startswith(AfterHoursSupportChatBot.MANUAL_KICK_START_TAG_KEYWORD):
                    start_after_hours_support_chatbot = True
                elif not is_within_working_hours:
                    start_after_hours_support_chatbot = True

        # start the chatbot with the conversationWrapper
        if start_after_hours_support_chatbot:
            ahs_chatbot = AfterHoursSupportChatBot(convo_wrapper=self.convo_wrapper)
            ahs_chatbot.answer()


if __name__ == "__main__":

    # dummy run, to test the dispatcher
    # using a real note, which is already in the conversation.
    # Get conversation_id from browser and use conversation wrapper to get the note_id
    note_id = '270867'

    data = {"resource_id": note_id, "resource_id_type": "Note", "event_type": "message.created", "changed_fields": []}
    dispatcher = ChatBotsDispatcher()
    dispatcher.endpoint(data)

