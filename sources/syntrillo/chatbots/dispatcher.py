# Path: ./sources/syntrillo/chatbots/dispatcher.py
import json

from typing import Tuple

from datetime import datetime
import pytz

from syntrillo.chatbots.conversation_wrapper import ChatBotConversationWrapper
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.helper_functions.html import remove_html_tags

from syntrillo.system.logger import logger

# import some chatbots
from syntrillo.chatbots.versions.v00_virtual_care_navigator.virtual_care_navigator import VirtualCareNavigator as v00_VirtualCareNavigator

from syntrillo.chatbots.versions.v01_after_hours_support.after_hours_support import AfterHoursSupportChatBot as v01_AfterHoursSupportChatBot

from syntrillo.chatbots.versions.v02_after_hours_virtual_assistant.after_hours_virtual_assistant import AfterHoursVirtualAssistant as v02_AfterHoursVirtualAssistant

from syntrillo.chatbots.versions.v03_care_plan_personalization_assistant.care_plan_personalization_assistant import CarePlanPersonalizationVirtualAssistant as v03_CarePlanPersonalizationVirtualAssistant


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

        TODO : comment

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
        convo_include_only_providers = self.convo_wrapper.does_convo_include_only_providers()
        conversation_owner = self.convo_wrapper.get_conversation_owner()
        patients = self.convo_wrapper.get_patients()
        is_org_staging = self.healthie_utils.is_org_staging()

        # logger
        logger.info(
            {
                "code" : "chatbots_dispatcher",
                "note_id" : note_id,
                "note_creator" : note_creator,
                "note_content" : note_content,
                "convo_includes_multiple_clients" : convo_includes_multiple_clients,
                "convo_include_only_providers" : convo_include_only_providers,
                "conversation_owner" : conversation_owner,
                "is_org_staging" : is_org_staging,
            }
        )

        # Remove HTML tags from note content, so that we can check for keywords at the start of the note
        note_content_clean = remove_html_tags(note_content)

        # chatbot to start or not
        v00_start_virtual_care_navigator = False
        v01_start_after_hours_support_chatbot = False
        v02_start_after_hours_virtual_assistant = False
        v03_start_care_plan_personalization_assistant = False

        # Get the current time in the EST timezone
        est = pytz.timezone('US/Eastern')
        current_time_est = datetime.now(est)

        # TODO: implement v02 and v03 if specific patient&providers (investors) are involved, using IDs and tags

        if is_org_staging:
            # We are in staging

            # Define the start and end time for the working hours (9 AM to 5 PM)
            start_time = current_time_est.replace(hour=9, minute=0, second=0, microsecond=0)
            end_time = current_time_est.replace(hour=17, minute=0, second=0, microsecond=0)
            is_within_working_hours = start_time <= current_time_est <= end_time

            if note_creator.is_provider():
                # place holder for direct provider interaction with chatbot

                if self.convo_wrapper.does_convo_includes_provider_with_tag(v03_CarePlanPersonalizationVirtualAssistant.CHATBOT_TAG) \
                    and convo_include_only_providers:
                        # we have a provider with the AI tag, and the conversation includes only providers
                    v03_start_care_plan_personalization_assistant = True

            else:
                # if the note creator is a patient and if content starts with a keyword
                if note_content_clean.startswith(v00_VirtualCareNavigator.MANUAL_KICK_START_TAG_KEYWORD):
                    v00_start_virtual_care_navigator = True

                elif note_content_clean.startswith(v01_AfterHoursSupportChatBot.MANUAL_KICK_START_TAG_KEYWORD):
                    v01_start_after_hours_support_chatbot = True

                elif note_content_clean.startswith(v02_AfterHoursVirtualAssistant.MANUAL_KICK_START_TAG_KEYWORD):
                    v02_start_after_hours_virtual_assistant = True

                # if the note creator is a patient start if after working hours
                if not is_within_working_hours:
                    # Not implemented yet
                    pass
                    # start_after_hours_support_chatbot = True

        else:
            # !!! We are in production !!!
            if note_creator.is_provider():
                # place holder for direct provider interaction with chatbot
                pass
            else:
                # if the note creator is a patient start if content starts with a keyword
                if note_content_clean.startswith(v02_AfterHoursVirtualAssistant.MANUAL_KICK_START_TAG_KEYWORD):
                    v02_start_after_hours_virtual_assistant = False  # Not implemented yet since PHI may be sent

                # if the note creator is a patient start if after working hours
                if not is_within_working_hours:
                    v02_start_after_hours_virtual_assistant = False  # Not implemented yet since PHI may be sent

        # start the chatbot with the conversationWrapper object
        if v01_start_after_hours_support_chatbot:
            ahs_chatbot = v01_AfterHoursSupportChatBot(convo_wrapper=self.convo_wrapper)
            ahs_chatbot.generate_responses()

        elif v02_start_after_hours_virtual_assistant:
            ahva_chatbot = v02_AfterHoursVirtualAssistant(convo_wrapper=self.convo_wrapper)
            ahva_chatbot.generate_responses()

        elif v03_start_care_plan_personalization_assistant:
            cppa_chatbot = v03_CarePlanPersonalizationVirtualAssistant(convo_wrapper=self.convo_wrapper)
            cppa_chatbot.generate_responses()

        elif v00_start_virtual_care_navigator:
            # TODO : implement legacy virtual care navigator chatbot
            pass


if __name__ == "__main__":

    # dummy run, to test the dispatcher
    # using a real note, which is already in the conversation.
    # Get conversation_id from browser and use conversation wrapper to get the note_id
    if False:
        note_id = '272047'

    if True:
        conversation_id = '1740910'
        wrapper = ChatBotConversationWrapper()
        log = wrapper.load_conversation_from_conversation_id(conversation_id)
        note_id = wrapper.get_last_note_id()

    data = {"resource_id": note_id, "resource_id_type": "Note", "event_type": "message.created", "changed_fields": []}
    dispatcher = ChatBotsDispatcher()
    dispatcher.endpoint(data)

