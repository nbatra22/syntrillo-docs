# Path: ./tests/tenovi/demo_hwi/tests_standalone/test00_api__device_types.py
# Path: ./tests/tenovi/tests_standalone/test00_api.py
import requests
from dotenv import load_dotenv
import os
import json

def get_device_types(api_key, client_domain):
    # Set up the URL for the API request
    URL = f"https://api2.tenovi.com/clients/{client_domain}/hwi/hwi-device-types/"

    # Set up the headers with the API key
    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/json"
    }

    try:
        # Make the GET request to the API
        response = requests.get(URL, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            device_types = response.json()
            return device_types
        else:
            # Handle unsuccessful requests
            print(f"Failed to retrieve device types: {response.status_code}")
            print(response.text)
            return None
    except requests.exceptions.RequestException as e:
        # Handle any exceptions that occur during the request
        print(f"An error occurred: {e}")
        return None

def print_pretty_devices(devices):
    for device in devices:
        print(json.dumps(device, indent=4, sort_keys=True))

if __name__ == "__main__":

    # Load the environment variables from the .env file
    load_dotenv(dotenv_path='.env')

    # Retrieve the API key and client domain from environment variables
    api_key = os.getenv('TENOVI_API_KEY')
    tenovi_client_domain = os.getenv('TENOVI_CLIENT_DOMAIN')

    if api_key is None:
        print("API key not found. Please check your .env file.")
        exit()

    if tenovi_client_domain is None:
        print("Client domain not found. Please check your .env file.")
        exit()

    # Call the function and print the results
    device_types = get_device_types(api_key, tenovi_client_domain)
    if device_types:
        print("Device Types:")
        print_pretty_devices(device_types)
