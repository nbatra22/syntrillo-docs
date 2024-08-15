
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

    # class attributes
    CHATBOT_TAG = "AfterHoursSupportChatbot"

    MANUAL_KICK_START_TAG_KEYWORD = "@ahs"

    INTRO_LINE_SHORT = "<p><b>After Hours Support Chatbot</b></p>"
    INTRO_LINE_LONG = "<p><b>Hi! I'm the After Hours Support Chatbot, answering in the absence of your provider.</b> I'm here to help you with any questions you have.</p>"


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

        # ------------------------------
        # step 1 : determine if tech or medical
        step1_messages = messages_raw.copy()

        # place the system content to the begining of the messages
        step1_setup_instructions = self.read_llm_file('step1a_setup_instructions.txt')
        step1_messages.insert(0, {'role': 'system', 'content': step1_setup_instructions})

        # append the question to the end of the messages
        step1_classification_query = self.read_llm_file('step1b_classification_query.txt')
        step1_messages.append({'role': 'user', 'content': step1_classification_query})

        # call LLM
        step1_llm_response = self.openai_call.send_messages(messages=step1_messages)

        # manage the response
        is_follow_up = ( 'follow' in step1_llm_response )
        is_technical = ( 'technical' in step1_llm_response )
        is_medical = ( 'medical' in step1_llm_response )

        # we go to step2 by default, unless some specific cases
        goto_step2 = True

        if is_follow_up:
            print("follow-up question")
            # do nothing, the next part will handle the follow-up
            pass
        else:
            # this is a new question

            # initiate the answer with the intro line
            if self.is_chatbot_already_in_convo is True:
                step1_response = self.INTRO_LINE_SHORT
            else:
                step1_response = self.INTRO_LINE_LONG

            # hardcoded answers for technical and medical questions
            if is_technical:
                step1_response += """
                <p>This is a technical question. Let me look into my database</p>
                """
            elif is_medical:
                step1_response += """
                <p>This is a medical question. I cannot help you directly, but I am going to ask you follow-up questions.</p>
                <p>If you need immediate help, please call 911 or go to the nearest emergency room.</p>
                """
            else:
                step1_response += """
                <p>I'm not sure if this is a technical or medical question. I'd suggest to wait for your provider to be available.</p>
                <p>If you need immediate help, please call 911 or go to the nearest emergency room.</p>
                """
                goto_step2 = False

            # send the answer
            self.convo_wrapper.create_note(
                content=step1_response,
                healthie_user_id=self.responder_user_id
            )

        # skip step2 and return
        if not goto_step2:
            print("not going to step2\nstep1_response:", step1_response)
            return

        # ------------------------------
        # step 2 : answer the question
        step2_messages = []
        if is_technical:
            # add system content
            step2_setup_instructions = self.read_llm_file('step2_path1a_setup_instructions_technical_support.txt')
            step2_messages.append({'role': 'system', 'content': step2_setup_instructions})

            # add the technical context
            step2_context_technical_healthie = self.read_llm_file('step2_path1b_context_technical_healthie.txt')
            step2_messages.append({
                'role': 'user',
                'content': json.dumps({
                    "topic": "Healthie technical information",
                    "information": step2_context_technical_healthie,
                    })
                })

            step2_context_technical_tenovi = self.read_llm_file('step2_path1b_context_technical_tenovi.txt')
            step2_messages.append({
                'role': 'user',
                'content': json.dumps({
                    "topic": "Tenovi technical information",
                    "information": step2_context_technical_tenovi,
                    })
                })

        elif is_medical:
            # add system content
            step2_setup_instructions = self.read_llm_file('step2_path2a_setup_instructions_medical_support.txt')
            step2_messages.append({'role': 'system', 'content': step2_setup_instructions})

            # add the medical context
            step2_context_medical = self.read_llm_file('step2_path2b_context_medical.txt')
            step2_messages.append({
                'role': 'user',
                'content': json.dumps({
                    "topic": "Medical information",
                    "information": step2_context_medical,
                    })
                })

        else:
            # print an error message
            print("ERROR: should not be here")
            return

        # add previous conversation
        step2_messages.extend(messages_raw)

        # call LLM
        step2_llm_response = self.openai_call.send_messages(messages=step2_messages)

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

