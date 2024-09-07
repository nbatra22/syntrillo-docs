# Path: ./sources/syntrillo/chatbots/versions/v02_after_hours_virtual_assistant/after_hours_virtual_assistant.py

import os
import json
import pytz

from datetime import datetime

from typing import Tuple

from syntrillo.api_healthie.tags import HealthieTags
from syntrillo.chatbots.conversation_wrapper import ChatBotConversationWrapper
from syntrillo.chatbots.openai_call import OpenAICall

class AfterHoursVirtualAssistant:
    """
    This class is responsible for answering messages after hours.

    It will reply as a chatbot if a chatbot user is available, otherwise it will reply as the provider user.

    Args:
        convo_wrapper (ChatBotConversationWrapper): The conversation wrapper.

    """

    # ------------------------------
    # class attributes

    # tag to identify the chatbot user
    CHATBOT_TAG = "AfterHoursVirtualAssistant"

    # keyword to activate the chatbot manually
    MANUAL_KICK_START_TAG_KEYWORD = "@ahva"

    # first time the chatbot is in the conversation
    INTRO_MESSAGE_FIRST_TIME = """
    <p>Hi! I’m the <b>After Hours Virtual Assistant</b>. Your care team is currently unavailable but let me see if I can help.</p>

    <p>I should mention that if you are experiencing an emergency or any symptoms of a possible stroke, your care team recommends that you call 911 immediately. According to the American Heart Association, symptoms of a stroke can include sudden numbness or weakness in the face, arm, or leg, especially on one side of the body; sudden confusion, trouble speaking, or understanding speech; sudden trouble seeing in one or both eyes; sudden trouble walking, dizziness, loss of balance or coordination; or a sudden severe headache with no known cause.</p>

    """

    # the chatbot is already in the conversation, given if long delay with last message
    INTRO_MESSAGE_SUBSEQUENT_TIMES = """
    <p>Hi! It’s me again, the <b>After Hours Virtual Assistant</b>. Your care team will not be available again until 8AM EST.</p>
    """

    INTRO_LINE_SHORT = "<p><b>After Hours Virtual Assistant</b></p>"

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


    def read_data_file(self, file_name):
        """
        Read content from a file in the 'data' directory.

        Parameters:
        - file_name (str): The name of the file to read.

        Returns:
        - str: The content of the specified file.
        """
        # Get the absolute path to the 'data' directory
        config_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), './data/'))
        file_path = os.path.join(config_dir, file_name)

        # Read and return the content of the file
        with open(file_path, 'r') as file:
            return file.read()


    def generate_responses(self):
        """
        answer the message

        # system : you're a chatbot. Previous conversation provided as list of json with 'who' (patient, provider, chatbot) and 'message' keys

        # determine if tech or medical

        # when content includes @ahs, it means you've been activated manually

        """

        # get all notes from the conversation as a message list
        messages_raw = self.convo_wrapper.get_all_notes_for_llm_as_openai_messages(
            chatbot_user_id=self.chatbot_user_id,
            keyword_to_remove_from_content=self.MANUAL_KICK_START_TAG_KEYWORD
        )

        # get datetime of the last message
        last_note_datetime = self.convo_wrapper.get_last_note_datetime()

        # ------------------------------
        # step1: deterministic messages
        step1_response = None
        if not self.is_chatbot_already_in_convo:
            # first time in the conversation
            step1_response = self.INTRO_MESSAGE_FIRST_TIME
        else:
            # use subsequent message if last message is more than 3 hours ago
            if last_note_datetime is not None:
                est = pytz.timezone('US/Eastern')
                current_time_est = datetime.now(est)
                time_diff = current_time_est - last_note_datetime
                if time_diff.total_seconds() > 3 * 3600:
                    step1_response = self.INTRO_MESSAGE_SUBSEQUENT_TIMES
                else:
                    step1_response = None
            else:
                # problem with the datetime
                # TODO : log warning
                step1_response = self.INTRO_MESSAGE_SUBSEQUENT_TIMES

        if step1_response is not None:
            # send the answer
            self.convo_wrapper.create_note(
                content=step1_response,
                healthie_user_id=self.responder_user_id
            )

        # ------------------------------
        # step2: LLM call
        step2_messages_for_llm = messages_raw.copy()

        # place the system content at the begining of the messages
        step2_setup_instructions = self.read_data_file('setup_instructions.md')
        step2_messages_for_llm.insert(0, {'role': 'system', 'content': step2_setup_instructions})

        # call LLM
        step2_llm_response = self.openai_call.send_messages(messages=step2_messages_for_llm)

        # if step2_llm_response does not start with a <p> or a <div>, add <div> at the beginning and </div> at the end
        if not step2_llm_response.startswith("<p>") and not step2_llm_response.startswith("<div>"):
            step2_llm_response = "<div>" + step2_llm_response + "</div>"

        # add the intro line if not already present in the response
        #  (the llm can add it by itself, but we want to make sure it's there)
        if self.INTRO_LINE_SHORT not in step2_llm_response:
            step2_response = self.INTRO_LINE_SHORT + step2_llm_response
        else:
            step2_response = step2_llm_response

        # send the answer
        self.convo_wrapper.create_note(
            content=step2_response,
            healthie_user_id=self.responder_user_id
        )

        print("step2_response:", step2_response)
        return

