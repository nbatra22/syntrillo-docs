# Path: ./tests/tenovi/tests_standalone/test00_api.py
import requests
from dotenv import load_dotenv
import os
import json

def get_device_types(api_key):
    # Set up the client domain and the URL for the API call
    CLIENT_DOMAIN = "syntrillo"
    URL = f"https://api2.tenovi.com/clients/{CLIENT_DOMAIN}/hwi/hwi-device-types/"

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

# Load the environment variables from the .env file
load_dotenv(dotenv_path='.env')

# Retrieve the API key from environment variables
api_key = os.getenv('TENOVI_API_KEY')

# Check if the API key was loaded successfully
if api_key:
    # Call the function and print the results
    device_types = get_device_types(api_key)
    if device_types:
        print("Device Types:")
        print_pretty_devices(device_types)
else:
    print("API key not found. Please check your .env file.")
