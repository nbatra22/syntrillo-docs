# Path: ./sources/syntrillo/charting_note_prefill/jackson.py

import os
import json
import io
import pymupdf
from typing import Tuple

# Import OpenAI package
from openai import OpenAI

from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets

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

            # ------------------------------
            # load openai secrets and environment variables
            # TODO : implement load_openai_secrets=True
            secrets = LocalEnvironmentAndSecrets()

            self.openai_api_key = os.getenv('OPENAI_API_KEY')

            self.log.append("Loaded API key from .env file.")

    def load_documents(self, documents_with_binary_content : list) -> None:
        """
        Load documents from the list of dictionaries with binary content. Extract text from the documents.

        Args:
            - documents_with_binary_content is a list of dictionaries with the following structure.

             [
                {
                "content": to be extracted as stream os bytes,
                "file_name" : document['file_name'],
                "file_type": document['file_content_type'],
                },
            ]
        """

        self.documents_with_binary_content = []

        # Process each binary document as if it was a file
        for document in documents_with_binary_content:

            if document.get('file_type') == 'application/pdf':
                # Use io.BytesIO to create a file-like object
                file_like_object = io.BytesIO(document.get('content'))

                # Use pymupdf to open the document from the file-like object
                doc = pymupdf.open(stream=file_like_object, filetype=document.get('file_type'))

                # extract text from the PDF
                text = self.__pdf_to_string(doc)
            else:
                text = document.get('content').decode("utf-8")

            self.documents_with_binary_content.append({
                "content": document.get('content'),
                "text": text,
                "file_name" : document['file_name'],
                "file_type": document['file_type'],
            })


    def __pdf_to_string(self, doc):
        text = ""
        # Iterate over each page in the PDF
        for page_num in range(len(doc)):
            # Get the page
            page = doc.load_page(page_num)
            # Extract text from the page
            text += page.get_text("text")

        return text

    def __generate_response(self, conversation: list) -> list:
        """
        Call the OpenAI API with the conversation prompt and return the response.

        Args:
            - conversation is a list of dictionaries with the following structure:

            [
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": "What is the weather like today?"
                }
            ]

        Returns:


        """

        #Sets up the client for the AI.
        client = OpenAI(api_key=self.openai_api_key)

        # Call the OpenAI API with the prompt
        #Could update model to 4 mini although it will use AWS llm in future.
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            response_format={ "type": "json_object" },
            messages= conversation,
            temperature= 0
        )

        #Extract the nested list from the response.
        data = response.choices[0].message.content

        return data


    def fill_form_from_discharge(
        self,
        form_answers_blank : list,
    ) -> Tuple [ list , list ] :
        """

        Uses an AI to generate a response to the questions provided in the form.

        Makes use of the discharge summary only to generate the responses. In future could add a new row to the google form specifying which document you want for each question.

        Args:

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

        Returns:
            - form_answers_filled is a list with the same structure as form_answers_blank, but with the 'answer' field filled-up based on the LLM_data information, and documents provided in the documents_with_binary_content list. The critical keys are:
                - "answer" : The answer to the question.
                - "custom_module_id" : The custom module ID. (ie the id of the question in the form)
                - "user_id" : The user ID.

            - a log

        """
        # ----------------------------------------------
        # find discharge summary, based on file name
        discharge_text = None
        for document in self.documents_with_binary_content:
            if 'discharge' in document.get('file_name').lower():
                discharge_text = document.get('text')
                break

        # return an error if no discharge summary is found
        if not discharge_text:
            log = {
                "success": False,
                "message": "No discharge summary found."
            }

            return form_answers_blank, log

        # ----------------------------------------------

        log = {
            "success": True
        }

        #Creates the list that will contain the responses
        form_answers_filled_out = []

        #Assigns the role of the chat bot.
        #In the future could provide a context document into the system instructions.
        #Would likely need a new parameter for the context to allow for flexibilty between various forms.
        temp_system = """You are a helpful assistant that gathers data from a document
        for the user. Only respond with data from the document that the user provides.
        Respond with a single python dictionary in a json format.
        """

        #loops through each question provided
        for form_answer in form_answers_blank:
            #defines the prompt for the AI from the form.
            prompt = form_answer.get('LLM_data').get("structure_item").get('llm_prompt')
            #prompt is the same as the qustion provided to the doctor if left as auto
            if prompt == "auto":
                prompt = form_answer.get('LLM_data').get("structure_item").get('question')

            #for "yes or no" special values adds insturctions to the end of the llm prompt.
            #In the future could create a helper function that works with any list of values provided.
            #Basic example of helper function provided below.
            if form_answer.get('LLM_data').get("structure_item").get('special_values') == "yes/no":
                prompt = prompt + " Answer ‘yes’ or ‘no’ for your response."

            #checks if there was a prompt provided to determine whether or not to respond.
            if not (prompt == None):
                #List of messages for the AI
                messages =  [{"role": "system", "content": temp_system},
                            {"role": "user", "content": f"{prompt} Document: {discharge_text}"}
                            ]

                #asks the AI, report the error in 'response' if anything goes wrong.
                response_ai = None
                try:
                    response_ai = self.__generate_response(messages)
                    response_json = self.__convert_json(response_ai)
                    #pulls the value from the json response
                    response_item = list(response_json.values())[0]
                except Exception as e:
                    response_item = "error : " + str(e)
                    self.log.append({
                        "error": f"Error in generating response for {form_answer.get('LLM_data').get('structure_item').get('question')}.",
                        "message": str(e),
                        "response_ai": response_ai
                    })
                    log["success"] = False

                # coerce the response to a string
                response = str(response_item)

                #add the answer to the list
                form_answers_filled_out.append({
                    "custom_module_id": form_answer['custom_module_id'],
                    "user_id": form_answer['user_id'],
                    "answer" : response,
                })

        log["class.log"] = self.log

        return form_answers_filled_out, log

    def __convert_json(self, response):
        """
        convert the response to a json object.
        """
        dictionary = json.loads(response)
        return dictionary

if __name__ == "__main__":

    # Instantiate the class
    prefill = ChartingNotePrefillJackson()

    print(json.dumps(prefill.log, indent=2, default=str))





