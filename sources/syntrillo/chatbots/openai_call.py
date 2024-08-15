import os
import json

# Import OpenAI package
from openai import OpenAI

from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets
from syntrillo.helper_functions.html import transform_to_safe_html


class OpenAICall:
    """

    """

    def __init__(self):
        # ------------------------------
        # load secrets and dotenv
        # TODO : implement load_openai_secrets=True
        secrets = LocalEnvironmentAndSecrets()

        # Retrieve the API key from environment variables
        self.openai_api_key = os.getenv('OPENAI_API_KEY')


    def send_messages(
        self,
        messages: list,
        temperature: float = 0.05,
        seed: int = 12,
        max_tokens: int = None,
        model: str = "gpt-4o",
    ) -> str:
        """
        Send messages to the OpenAI API and return the assistant's reply.

        model="gpt-3.5-turbo-1106"
           - 30 times less expensive than gpt 4 : https://openai.com/pricing , 16K context window

        "gpt-4o" : $5.00 / 1M input tokens

        "gpt-4-turbo" : $10.00 / 1M tokens

        Args:
            messages (list): The list of messages to send to the OpenAI API, where each message is a dictionary with the keys 'role' and 'content'. Roles can be 'system', 'user' or 'assistant'.
            temperature (float): The sampling temperature to use when generating the assistant's reply.
            seed (int): The random seed to use when generating the assistant's reply.
            max_tokens (int): The maximum number of tokens to generate in the assistant's reply.
            model (str): The model to use for generating the assistant's reply.

        Returns:
            str: The assistant's reply as a safe HTML string

        """
        # call openAI API
        #   ; https://platform.openai.com/docs/api-reference/chat/create
        openai_client = OpenAI(
            api_key=self.openai_api_key,
        )

        response = openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            seed=seed,
        )

        self._response = response

        # Extract the assistant's reply from the new structure
        assistant_reply = response.choices[0].message.content

        # make the assistant reply safe
        safe_assistant_reply = transform_to_safe_html(assistant_reply.strip())

        return safe_assistant_reply

