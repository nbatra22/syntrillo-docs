import os
import requests
import inspect
import json
from dotenv import load_dotenv

class TenoviAuth:
    def __init__(self, dotenv_path='.env'):
        # paths have to be hard-coded at PythonAnywhere
        if os.path.exists('/home/syntrillo/_this_is_PythonAnywhere_') and dotenv_path == ".env":
            dotenv_path = '/home/syntrillo/Syntrillo_Clinic/.env'

        # Load the environment variables from the specified file
        load_dotenv(dotenv_path=dotenv_path)

        # Retrieve the API key from environment variables
        self.api_key = os.getenv('TENOVI_API_KEY')

        # Ensure the API key was successfully loaded
        if not self.api_key:
            raise ValueError("API key not found. Please check your .env file.")

    def get_headers(self):
        # Return the headers needed for the API calls
        return {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }

    def make_get_request(self, url, params=None):
        """
        Makes a GET request to the provided URL and handles the response.

        Args:
            url (str): The URL to make the GET request to.
            params (dict, optional): Query parameters to include in the request.

        Returns:
            dict or None: The JSON response if the request was successful, None otherwise.
        """
        caller = inspect.stack()[1].function
        try:
            response = requests.get(url, headers=self.get_headers(), params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to retrieve data in {caller}: {response.status_code}")
                print(response.text)
                return None
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None

    def make_post_request(self, url, data):
        """
        Makes a POST request to the provided URL and handles the response.

        Args:
            url (str): The URL to make the POST request to.
            data (dict): The payload to send with the POST request.

        Returns:
            dict or None: The JSON response if the request was successful, None otherwise.
        """
        caller = inspect.stack()[1].function
        try:
            response = requests.post(url, headers=self.get_headers(), json=data)
            if response.status_code == 201:  # Typically, successful POST requests return a 201 status code
                return response.json()
            else:
                print(f"Failed to post data in {caller}: {response.status_code}")
                print(response.text)
                return None
        except requests.exceptions.RequestException as e:
            print(f"An error occurred in {caller}: {e}")
            return None

    @staticmethod
    def print_pretty_json(data):
        print(json.dumps(data, indent=4, sort_keys=True))

