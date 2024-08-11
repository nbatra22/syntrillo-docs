
import os
import json

from typing import Tuple

from syntrillo.api_healthie.tags import HealthieTags
from syntrillo.chatbots.conversation_wrapper import ChatBotConversationWrapper
from syntrillo.chatbots.openai_call import OpenAICall

class AfterHoursSupportChatBot:
    """
    This class is responsible for answering messages after hours.

    It will reply as a chatbot if a chatbot user is available, otherwise it will reply as the provider user.

    Args:
        convo_wrapper (ChatBotConversationWrapper): The conversation wrapper.

    """

    CHATBOT_TAG = "AfterHoursSupportChatbot"

    MANUAL_KICK_START_TAG_KEYWORD = "@ahs"

    INTRO_LINE_SHORT = "<p><b>After Hours Support Chatbot</b></p>"
    INTRO_LINE_LONG = "<p><b>Hi! I'm the After Hours Support Chatbot, answering in the absence of your provider.</b> I'm here to help you with any questions you have.</p>"

    # class attributes
    _convo_wrapper = None
    _chatbot_user_id = None

    def __init__(self, convo_wrapper: ChatBotConversationWrapper):

        # OpenAI call
        self.openai_call = OpenAICall()

        # ------------------------------
        # this includes the lastest note and the whole conversation
        self._convo_wrapper = convo_wrapper

        # ------------------------------
        # is there an user with my tag?
        #  : if yes, I'll use this user to answer
        #  : if no, I'll use the provider user
        tags = HealthieTags()
        uids = tags.get_user_ids_by_tag_name(self.CHATBOT_TAG)
        if uids:
            if len(uids) == 1:
                self._chatbot_user_id = uids[0]
            else:
                self._chatbot_user_id = None
                raise ValueError(f"More than one user with tag {self.CHATBOT_TAG}")
        else:
            self._chatbot_user_id = None

        if self._chatbot_user_id:
            self.answer_by_id = self._chatbot_user_id
            self.chatbot_user_available_to_answer = True
        else:
            self.answer_by_id = self._convo_wrapper.get_conversation_owner().healthie_user_id
            self.chatbot_user_available_to_answer = False

        # ------------------------------
        # Detect if the chatbot has already answered
        if self.chatbot_user_available_to_answer:
            self.is_chatbot_already_in_convo = self._convo_wrapper.is_user_in_convo(self._chatbot_user_id)
        else:
            self.is_chatbot_already_in_convo = None


    def read_llm_file(self, file_name):
        """
        Read content from a file in the 'llm' directory.

        Parameters:
        - file_name (str): The name of the file to read.

        Returns:
        - str: The content of the specified file.
        """
        # Get the absolute path to the 'llm' directory
        config_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), './llm/ahs/'))
        file_path = os.path.join(config_dir, file_name)

        # Read and return the content of the file
        with open(file_path, 'r') as file:
            return file.read()


    def answer(self):
        """
        answer the message

        # system : you're a chatbot. Previous conversation provided as list of json with 'who' (patient, provider, chatbot) and 'message' keys

        # determine if tech or medical

        # when content includes @ahs, it means you've been activated manually

        """

        # get all notes from the conversation as a message list
        messages_raw = self._convo_wrapper.get_all_notes_for_llm_as_openai_messages(
            chatbot_user_id=self._chatbot_user_id,
            keyword_to_remove_from_content=self.MANUAL_KICK_START_TAG_KEYWORD
        )

        # ------------------------------
        # step 1 : determine if tech or medical
        messages_step1 = messages_raw.copy()

        # place the system content to the begining of the messages
        system_content = self.read_llm_file('instructions_init.txt')
        messages_step1.insert(0, {'role': 'system', 'content': system_content})

        # append the question to the end of the messages
        question = self.read_llm_file('question_technical_or_medical.txt')
        messages_step1.append({'role': 'user', 'content': question})

        # call LLM
        response_step1 = self.openai_call.send_messages(messages=messages_step1)

        # manage the response
        is_follow_up = ( 'followup' in response_step1 )
        is_technical = ( 'technical' in response_step1 )
        is_medical = ( 'medical' in response_step1 )
        if not is_follow_up:
            if self.is_chatbot_already_in_convo is True:
                answer_step1 = self.INTRO_LINE_SHORT
            else:
                answer_step1 = self.INTRO_LINE_LONG

            if is_technical:
                answer_step1 += """
                <p>This is a technical question. Let me look into my database</p>
                """
            elif is_medical:
                answer_step1 += """
                <p>This is a medical question. I cannot help you direclty, but I am going to ask you follow-up questions</p>
                <p>If you need immediate help, please call 911 or go to the nearest emergency room.</p>
                """
            else:
                answer_step1 += """
                <p>I'm not sure if this is a technical or medical question. I'd suggest to wait for your provider to be available.</p>
                <p>If you need immediate help, please call 911 or go to the nearest emergency room.</p>
                """

            # send the answer
            self._convo_wrapper.create_note(
                content=answer_step1,
                healthie_user_id=self.answer_by_id
            )

        if not is_technical and not is_medical:
            return

        # ------------------------------
        # step 2 : answer the question
        messages_step2 = []
        if is_technical:
            # add system content
            system_content = self.read_llm_file('instructions_technical.txt')
            messages_step2.append({'role': 'system', 'content': system_content})

            # add the technical context
            context_healthie = self.read_llm_file('technical_context_healthie.txt')
            messages_step2.append({
                'role': 'user',
                'content': json.dumps({
                    "topic": "Healthie technical information",
                    "information": context_healthie,
                    })
                })

            context_tenovi = self.read_llm_file('technical_context_tenovi.txt')
            messages_step2.append({
                'role': 'user',
                'content': json.dumps({
                    "topic": "Tenovi technical information",
                    "information": context_tenovi,
                    })
                })

        elif is_medical:
            # add system content
            system_content = self.read_llm_file('instructions_medical.txt')
            messages_step2.append({'role': 'system', 'content': system_content})

            # add the medical context
            context = self.read_llm_file('medical_context.txt')
            messages_step2.append({
                'role': 'user',
                'content': json.dumps({
                    "topic": "Medical information",
                    "information": context,
                    })
                })

        else:
            return

        # add previous conversation
        messages_step2.extend(messages_raw)

        # call LLM
        response_step2 = self.openai_call.send_messages(messages=messages_step2)

        response_step2_with_intro = self.INTRO_LINE_SHORT + " <div> " + str(response_step2) + " </div> "

        # send the answer
        self._convo_wrapper.create_note(
            content=response_step2_with_intro,
            healthie_user_id=self.answer_by_id
        )

        return

