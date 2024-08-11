
import os
import json

from typing import Tuple

from syntrillo.api_healthie.tags import HealthieTags
from syntrillo.chatbots.conversation_wrapper import ChatBotConversationWrapper
from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets

class AfterHoursSupportChatBot:
    """
    This class is responsible for answering messages after hours.

    It will reply as a chatbot if a chatbot user is available, otherwise it will reply as the provider user.

    Args:
        convo_wrapper (ChatBotConversationWrapper): The conversation wrapper.

    """

    CHATBOT_TAG = "AfterHoursSupportChatbot"

    # class attributes
    _convo_wrapper = None
    _chatbot_user_id = None

    def __init__(self, convo_wrapper: ChatBotConversationWrapper):

        # ------------------------------
        # load secrets and dotenv
        # TODO : implement load_openai_secrets=True
        secrets = LocalEnvironmentAndSecrets()

        # Retrieve the API key from environment variables
        self.openai_api_key = os.getenv('OPENAI_API_KEY')

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


    def answer(self):
        """
        answer the message

        """

        if self._chatbot_user_id:
            answer_by_id = self._chatbot_user_id
        else:
            answer_by_id = self._convo_wrapper.get_conversation_owner().healthie_user_id

        self._convo_wrapper.create_note(
            content="hello",
            healthie_user_id=answer_by_id
        )

