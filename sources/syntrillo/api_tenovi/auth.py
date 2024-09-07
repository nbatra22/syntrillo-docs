# Path: ./sources/syntrillo/api_tenovi/auth.py

import requests
import inspect
import json
from typing import Tuple

from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets


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

        # ------------------------------
        # load tenovi secrets
        secrets = LocalEnvironmentAndSecrets(load_tenovi_hwi_secrets=True)

        # ---
        # retrieve the client domain
        self.client_domain = secrets.get_tenovi_hwi_client_domain()

        if not self.client_domain:
            raise ValueError("Tenovi client domain not found. Please check aws secrets manager or .env file.")

        # ---
        # ensure the TENOVI_BASE_URL_ROOT ends with a trailing slash
        if not self.TENOVI_BASE_URL_ROOT.endswith('/'):
            self.TENOVI_BASE_URL_ROOT += '/'

        # set the base url for the Tenovi API calls
        #  : must end with a trailing slash
        self.base_url = f"{self.TENOVI_BASE_URL_ROOT}{self.client_domain}"

        if not self.base_url.endswith('/'):
            self.base_url += '/'

        # ---
        # Retrieve the API key
        self.api_key=secrets.get_tenovi_hwi_api_key()

        # Ensure the API key was successfully loaded
        if not self.api_key:
            raise ValueError("Tenovi API key not found. Please check aws secrets manager or .env file.")


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
        timeout: int = 10,
        verbose: bool = False
        ) -> Tuple[dict, dict]:
        """
        Makes a GET request to the provided URL and handles the response.

        Args:
            url (str): The URL to make the GET request to.
            params (dict, optional): Query parameters to include in the request.
            timeout (int, optional): The number of seconds to wait for the server to send data before giving up.

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
            response = requests.get(full_url, headers=self.get_headers(), params=params, timeout=timeout)
            if response.status_code == 200:
                json_output = response.json()
                log = {
                    "success": True,
                    "message": f"Successfully got data in {caller}"
                }
                return json_output, log
            else:
                if verbose:
                    print(f"Failed to get data in {caller}: {response.status_code}")
                    print(response.text)
                log = {
                    "success": False,
                    "message": f"Failed to get data in {caller}: {response.status_code}",
                    "code": response.status_code,
                    "response": response.json() if response.text else None,
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

