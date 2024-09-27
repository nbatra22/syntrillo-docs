# Path: ./sources/syntrillo/chatbots/versions/v02_after_hours_virtual_assistant/after_hours_virtual_assistant.py

import os
import json
import pytz
import requests

from datetime import datetime

from typing import Tuple

from syntrillo.system.logger import logger

from syntrillo.api_healthie.tags import HealthieTags
from syntrillo.chatbots.conversation_wrapper import ChatBotConversationWrapper
from syntrillo.chatbots.openai_call import OpenAICall

class AfterHoursVirtualAssistantBedrock:
    """
    This class helps providers builind a personalized care plan.

    Args:
        convo_wrapper (ChatBotConversationWrapper): The conversation wrapper.

    """

    # ------------------------------
    # class attributes

    # tag to identify the chatbot user
    CHATBOT_TAG = "AfterHoursVirtualAssistantBedrock"

    # keyword to activate the chatbot manually
    MANUAL_KICK_START_TAG_KEYWORD = "@bahva"


    def __init__(self, convo_wrapper: ChatBotConversationWrapper):

        # OpenAI call
        self.openai_call = OpenAICall()

        # ------------------------------
        # this includes the lastest note and the whole conversation
        self.convo_wrapper = convo_wrapper

        # ------------------------------
        # is there an user with my tag?
        #  : if yes, I'll use this user to answer
        #  : if no, I'll use the provider user
        tags = HealthieTags()
        uids = tags.get_user_ids_by_tag_name(self.CHATBOT_TAG)
        if uids:
            if len(uids) == 1:
                self.chatbot_user_id = uids[0]
            else:
                self.chatbot_user_id = None
                raise ValueError(f"More than one user with tag {self.CHATBOT_TAG}")
        else:
            self.chatbot_user_id = None

        if self.chatbot_user_id:
            self.responder_user_id = self.chatbot_user_id
            self.chatbot_user_available_to_answer = True
        else:
            self.responder_user_id = self.convo_wrapper.get_conversation_owner().healthie_user_id
            self.chatbot_user_available_to_answer = False

        # ------------------------------
        # Detect if the chatbot has already answered
        if self.chatbot_user_available_to_answer:
            self.is_chatbot_already_in_convo = self.convo_wrapper.is_user_in_convo(self.chatbot_user_id)
        else:
            self.is_chatbot_already_in_convo = None


    def generate_responses(self):
        """
        answer the message

        """

        # the Healthie conversation (list of 'notes') is in self.convo_wrapper
        notes = self.convo_wrapper.get_all_notes_for_llm()

        # get last note
        # expected format :
        #   "last_note":{"who":"provider or chatbot","content":"<p>hello</p>","created_at":"2024-09-26 12:14:25 -0400"}}
        if notes is None:
            last_note = None
        else:
            last_note = notes[-1]

        logger.info({
            "message": "AfterHoursVirtualAssistantBedrock.generate_responses",
            "last_note": last_note
        })

        # create the response
        response = "AfterHoursVirtualAssistantBedrock.generate_responses says hello!"

        if False:
            llm_response = requests.post('http://10.0.190.145/query', headers= {'Content-Type': 'application/json'} , data = json.dumps({
                "query": last_note["content"],
                "model": "claude-3-5-sonnet"}))
            response = json.loads(llm_response.text)['answer']

        # send the answer to the Healthie chat
        self.convo_wrapper.create_note(
            content=response,
            healthie_user_id=self.responder_user_id
        )

        return

