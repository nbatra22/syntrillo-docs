# Path: ./sources/syntrillo/api_tenovi/auth.py

import os
import requests
import inspect
import json

from syntrillo.system.dot_env_loader import DotEnvFileLoader

class TenoviAuth:
    """
    A class to handle authentication with the Tenovi API

    Attributes:
        client_domain (str): The client domain for the Tenovi API calls.
        base_url (str): The base URL for the Tenovi API calls.
        api_key (str): The API key for the Tenovi API calls.
    """

    # The base URL for the Tenovi API calls, including API version
    TENOVI_BASE_URL_ROOT="https://api2.tenovi.com/clients/"

    def __init__(self):

        # Load the .env file based on the environment to retrieve the client domain and API key
        _ = DotEnvFileLoader()

        # retrieve the client domain from the environment variables
        self.client_domain = os.getenv('TENOVI_CLIENT_DOMAIN')
        if not self.client_domain:
            raise ValueError("Tenovi client domain not found. Please check your .env file.")

        # Ensure the client domain has a trailing slash
        if not self.client_domain.endswith('/'):
            self.client_domain += '/'

        # set the base url for the Tenovi API calls
        #  : must end with a trailing slash
        self.base_url = f"{self.TENOVI_BASE_URL_ROOT}{self.client_domain}/"

        # Retrieve the API key from environment variables
        self.api_key = os.getenv('TENOVI_API_KEY')

        # Ensure the API key was successfully loaded
        if not self.api_key:
            raise ValueError("Tenovi API key not found. Please check your .env file.")

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
        full_url = self.base_url + url
        caller = inspect.stack()[1].function
        try:
            response = requests.get(full_url, headers=self.get_headers(), params=params)
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
        full_url = self.base_url + url
        caller = inspect.stack()[1].function
        try:
            response = requests.post(full_url, headers=self.get_headers(), json=data)
            if response.status_code == 201:  # Typically, successful POST requests return a 201 status code
                return response.json()
            else:
                print(f"Failed to post data in {caller}: {response.status_code}")
                print(response.text)
                return None
        except requests.exceptions.RequestException as e:
            print(f"An error occurred in {caller}: {e}")
            return None

    def make_patch_request(self, url, data):
        """
        Makes a PATCH request to the provided URL and handles the response.

        Args:
            url (str): The URL to make the PATCH request to.
            data (dict): The payload to send with the PATCH request.

        Returns:
            dict or None: The JSON response if the request was successful, None otherwise.
        """
        full_url = self.base_url + url
        caller = inspect.stack()[1].function
        try:
            response = requests.patch(full_url, headers=self.get_headers(), json=data)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to patch data in {caller}: {response.status_code}")
                print(response.text)
                return None
        except requests.exceptions.RequestException as e:
            print(f"An error occurred in {caller}: {e}")
            return None

    @staticmethod
    def print_pretty_json(data):
        print(json.dumps(data, indent=4, sort_keys=True))

