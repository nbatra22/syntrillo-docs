
import os
import json

# Import OpenAI package
from openai import OpenAI

from syntrillo.system.dot_env_loader import DotEnvFileLoader

class ChartingNotePrefillJackson:

    """
    Class that accept a dictionary in the LLM data structure and a list of binary documents
    and returns an answer to the question on the form.
    """

    # class attributes
    openai_api_key : str = None
    log : list = []

    def __init__(self) -> None:
        # load api key
        self.load_api_key()

    def load_api_key(self):
        """
        Load the OpenAI API key from the environment variables.
        """
        try:
            # Attempt to import the Colab specific module
            from google.colab import userdata

            # If running in Google Colab, fetch the API key using userdata
            self.openai_api_key = userdata.get('OpenAI_Key')

            self.log.append("Loaded API key from Google Colab.")

        except ImportError:
            # Not running in Google Colab

            # Load the .env file based on the environment to retrieve the client domain and API key
            _ = DotEnvFileLoader()

            self.openai_api_key = os.getenv('OPENAI_API_KEY')

            self.log.append("Loaded API key from .env file.")


    def runme(
        self,
        form_answers_blank : list,
        documents_with_binary_content : list
    ) -> list :
        """

        Args:
            - documents_with_binary_content is a list of dictionaries with the following structure. The objective is to extract the text from the 'content' field and fill-up the 'answer' field in the form_answers_blank list.

            - form_answers_blank is a list with the following structure. The objective is to fill-up 'answer' field based on the LLM_data information, and documents provided in the documents_with_binary_content list.

            [
                {
                    "LLM_data": {
                        "structure_item": {
                            "add_not_applicable": null,
                            "add_unknown": null,
                            "comment": null,
                            "display": "number",
                            "internal_description": null,
                            "internal_name": "openings_am",
                            "llm_prompt": "pick a random number between 0 and 5.",
                            "question": "Number of AM opening(s)",
                            "special_values": null,
                            "sublabel": "Leave blank if you have to use daily total",
                            "type": null,
                            "values": null
                        },
                        "structure_metadata": {
                            "description": "Used for the assessment of Medication Adherence. Give number of openings expected in the mornings, evenings, or total daily",
                            "internal_name": "tenovi_pillbox_expectations",
                            "name": "Tenovi Pillbox Expectations",
                            "prefill": false,
                            "type": "Charting Notes (for providers)",
                            "use_for_charting": true,
                            "use_for_program": false,
                            "version": "0.2"
                        }
                    },
                    "answer": null,
                    "custom_module_id": "11944464",
                    "user_id": "1035117"
                },


        """

        return form_answers_blank


if __name__ == "__main__":

    # Instantiate the class
    prefill = ChartingNotePrefillJackson()

    print(json.dumps(prefill.log, indent=2, default=str))




