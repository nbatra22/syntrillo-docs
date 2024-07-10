# Path: ./sources/syntrillo/api_tenovi/auth.py

import os
import re
import requests
import inspect
import json
from typing import Tuple

from syntrillo.system.dot_env_loader import DotEnvFileLoader

def get_secrets(secret_arn):
    try:
        get_secret_value_response = requests.get(
            f"http://localhost:2773/secretsmanager/get?secretId={secret_arn}",
            headers={"X-AWS-Parameters-Secrets-Token": os.environ.get('AWS_SESSION_TOKEN')},
        )
        get_secret_value_response.raise_for_status()  # Raise an exception for non-2xx status codes
    except requests.exceptions.RequestException as e:
        # Handle exceptions related to the HTTP request
        # if "an unexpected error occurred while executing request" in the response text => check lammbda permissions to read in secrets manager
        raise Exception(f"Error fetching secret [{get_secret_value_response.text}]: {e}")

    try:
        secret_value = get_secret_value_response.text
        secret_dict = json.loads(secret_value)
    except json.JSONDecodeError as e:
        # Handle exceptions related to JSON decoding
        raise Exception(f"Error decoding secret value [{get_secret_value_response.text}]: {e}")

    try:
        secrets_string = secret_dict["SecretString"]
    except KeyError as e:
        # Handle exceptions related to missing "SecretString" key
        raise Exception(f"Error retrieving SecretString: {e}")
    
    try:
        secrets_dict=json.loads(secrets_string)
        return secrets_dict
    except json.JSONDecodeError as e:
        # Handle exceptions related to not well formated secret string (non json)
        raise Exception(f"Error decoding secrets (should be in json format in aws secrets manager): {e}")

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

    # class variables
    client_domain: str = None
    base_url: str = None
    api_key: str = None

    def __init__(self):

        if os.getenv('AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN') != None:
            # This test means we are in the lambda function
            
            # retrieve secrets in aws secrets manager
            tenovi_hwi_secrets=get_secrets(os.getenv('AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN'))

            # retrieve the client domain from the environment variables
            self.client_domain=tenovi_hwi_secrets["tenoviHwiClientDomain"]
            if not self.client_domain:
                raise ValueError("Tenovi client domain not found. Please check aws secrets manager.")

            # ensure the TENOVI_BASE_URL_ROOT ends with a trailing slash
            if not self.TENOVI_BASE_URL_ROOT.endswith('/'):
                self.TENOVI_BASE_URL_ROOT += '/'

            # set the base url for the Tenovi API calls
            #  : must end with a trailing slash
            self.base_url = f"{self.TENOVI_BASE_URL_ROOT}{self.client_domain}"

            if not self.base_url.endswith('/'):
                self.base_url += '/'

            # Retrieve the API key from environment variables
            self.api_key=tenovi_hwi_secrets["tenoviHwiApiKey"]

            # Ensure the API key was successfully loaded
            if not self.api_key:
                raise ValueError("Tenovi API key not found. Please check aws secrets manager.")

        else:
            # Load the .env file based on the environment to retrieve the client domain and API key
            _ = DotEnvFileLoader()

            # retrieve the client domain from the environment variables
            self.client_domain = os.getenv('TENOVI_CLIENT_DOMAIN')
            if not self.client_domain:
                raise ValueError("Tenovi client domain not found. Please check your .env file.")

            # ensure the TENOVI_BASE_URL_ROOT ends with a trailing slash
            if not self.TENOVI_BASE_URL_ROOT.endswith('/'):
                self.TENOVI_BASE_URL_ROOT += '/'

            # set the base url for the Tenovi API calls
            #  : must end with a trailing slash
            self.base_url = f"{self.TENOVI_BASE_URL_ROOT}{self.client_domain}"

            if not self.base_url.endswith('/'):
                self.base_url += '/'

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

    def construct_url(self, url: str) -> str:
        """
        Constructs the full URL for the provided URL.

        Args:
            url (str): The URL to construct the full URL for.

        Returns:
            str: The full URL for the provided URL.
        """
        # if self.base_url ends with a trailing slash and url starts with a slash, remove one of them
        if self.base_url.endswith('/') and url.startswith('/'):
            return self.base_url + url[1:]
        else:
            return self.base_url + url

    def make_get_request(
        self,
        url: str,
        params: dict = None,
        verbose: bool = False
        ) -> Tuple[dict, dict]:
        """
        Makes a GET request to the provided URL and handles the response.

        Args:
            url (str): The URL to make the GET request to.
            params (dict, optional): Query parameters to include in the request.

        Returns a tupple:
        - dict or None: The JSON response if the request was successful, None otherwise.
        - log of the API call
        """
        # Construct the full URL for the GET request
        full_url = self.construct_url(url)

        # Get the name of the calling function for logging purposes
        caller = inspect.stack()[1].function

        # Try converting the data to a JSON string. If this fails, return an error log.
        #   : this will fail if the data is not JSON serializable, for example if it includes uuid objects
        if params:
            try:
                temp = json.dumps(params)
            except Exception as e:
                log = {
                    "success": False,
                    "message": f"A json.dumps error occurred in {caller}: {e}",
                    "data": params,
                }
                return None, log

        # Make the GET request
        try:
            response = requests.get(full_url, headers=self.get_headers(), params=params)
            if response.status_code == 200:
                json_output = response.json()
                log = {
                    "success": True,
                    "message": f"Successfully posted data in {caller}"
                }
                return json_output, log
            else:
                if verbose:
                    print(f"Failed to post data in {caller}: {response.status_code}")
                    print(response.text)
                log = {
                    "success": False,
                    "message": f"Failed to get data in {caller}: {response.status_code}",
                    "error": response.json() if response.text else None,
                }
                return None, log

        # Handle any exceptions that occur during the GET request
        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"An error occurred in {caller}: {e}")
            log = {
                "success": False,
                "message": f"An error occurred in {caller}: {e}"
            }
            return None, log


    def make_post_request(
        self,
        url: str,
        data: dict,
        verbose: bool = False
        ) -> Tuple[dict, dict]:
        """
        Makes a POST request to the provided URL and handles the response.

        Args:
            url (str): The URL to make the POST request to.
            data (dict): The payload to send with the POST request.

        Returns a tupple:
        - dict : The JSON response if the request was successful or not.
        - log of the API call
        """

        # Construct the full URL for the POST request
        full_url = self.construct_url(url)

        # Get the name of the calling function for logging purposes
        caller = inspect.stack()[1].function

        # Try converting the data to a JSON string. If this fails, return an error log.
        #   : this will fail if the data is not JSON serializable, for example if it includes uuid objects
        try:
            temp = json.dumps(data)
        except Exception as e:
            log = {
                "success": False,
                "message": f"A json.dumps error occurred in {caller}: {e}",
                "data": data,
            }
            return None, log

        # Make the POST request
        try:
            response = requests.post(full_url, headers=self.get_headers(), json=data) # json.dumps(data, default=str)
            if response.status_code == 201:  # Typically, successful POST requests return a 201 status code
                json_output = response.json()
                log = {
                    "success": True,
                    "message": f"Successfully posted data in {caller}",
                }
                return json_output, log
            else:
                if verbose:
                    print(f"Failed to post data in {caller}: {response.status_code}")
                    print(response.text)
                log = {
                    "success": False,
                    "message": f"Failed to post data in {caller}: {response.status_code}",
                    "error": response.json() if response.text else None,
                }
                return None, log

        # Handle any exceptions that occur during the POST request
        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"An error occurred in {caller}: {e}")
            log = {
                "success": False,
                "message": f"An error occurred in {caller}: {e}",
            }
            return None, log


    def make_patch_request(
        self,
        url: str,
        data: dict,
        verbose: bool = False
        ) -> Tuple[dict, dict]:
        """
        Makes a PATCH request to the provided URL and handles the response.

        Args:
            url (str): The URL to make the PATCH request to.
            data (dict): The payload to send with the PATCH request.
            verbose (bool, optional): Whether to print verbose output.

        Returns a tupple:
        - dict or None: The JSON response if the request was successful, None otherwise.
        - log of the API call
        """

        # Construct the full URL for the PATCH request
        full_url = self.construct_url(url)

        # Get the name of the calling function for logging purposes
        caller = inspect.stack()[1].function

        # Try converting the data to a JSON string. If this fails, return an error log.
        #   : this will fail if the data is not JSON serializable, for example if it includes uuid objects
        try:
            temp = json.dumps(data)
        except Exception as e:
            log = {
                "success": False,
                "message": f"A json.dumps error occurred in {caller}: {e}",
                "data": data,
            }
            return None, log

        # Make the PATCH request
        try:
            response = requests.patch(full_url, headers=self.get_headers(), json=data)
            if response.status_code == 200:
                json_output = response.json()
                log = {
                    "success": True,
                    "message": f"Successfully posted data in {caller}"
                }
                return json_output, log
            else:
                if verbose:
                    print(f"Failed to path data in {caller}: {response.status_code}")
                    print(response.text)
                log = {
                    "success": False,
                    "message": f"Failed to get data in {caller}: {response.status_code}",
                    "error": response.json() if response.text else None,
                }
                return None, log

        # Handle any exceptions that occur during the PATCH request
        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"An error occurred in {caller}: {e}")
            log = {
                "success": False,
                "message": f"An error occurred in {caller}: {e}"
            }
            return None, log


    def make_delete_request(self, url: str, verbose: bool = False) -> Tuple[dict, dict]:
        """
        Makes a DELETE request to the provided URL and handles the response.

        Args:
            url (str): The URL to make the DELETE request to.
            verbose (bool, optional): Whether to print verbose output.

        Returns a tupple:
        - dict or None: The JSON response if the request was successful, None otherwise.
        - log of the API call
        """

        # Construct the full URL for the DELETE request
        full_url = self.construct_url(url)

        # Get the name of the calling function for logging purposes
        caller = inspect.stack()[1].function

        # Make the DELETE request
        try:
            response = requests.delete(full_url, headers=self.get_headers())
            if response.status_code == 204:
                log = {
                    "success": True,
                    "message": f"Successfully deleted data in {caller}"
                }
                return {}, log
            else:
                if verbose:
                    print(f"Failed to delete data in {caller}: {response.status_code}")
                    print(response.text)
                log = {
                    "success": False,
                    "message": f"Failed to delete data in {caller}: {response.status_code}",
                    "error": response.json() if response.text else None,
                }
                return None, log

        # Handle any exceptions that occur during the DELETE request
        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"An error occurred in {caller}: {e}")
            log = {
                "success": False,
                "message": f"An error occurred in {caller}: {e}"
            }
            return None, log


    @staticmethod
    def print_pretty_json(data):
        print(json.dumps(data, indent=4, sort_keys=True))

