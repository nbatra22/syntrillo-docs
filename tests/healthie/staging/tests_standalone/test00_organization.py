# ./Syntrillo_Clinic/tests/healthie/staging/tests_standalone/test00_organization.py

# using conda 'syntrillo' environment

# query from https://docs.gethealthie.com/docs/#querying-filled-out-forms
# use https://docs.gethealthie.com/docs/explorer to get parameters

import sys
import requests
import os
import json
from dotenv import load_dotenv

# Set up the GraphQL query
query = '''
query getOrganization($id: ID) {
  organization(id: $id) {
    id
    name
    location {
      city
      country
    }
  }
}
'''

# Load environment variables from .env file
load_dotenv(dotenv_path=".env.Healthie.staging")

# Get the API key from the environment variables
api_key = os.getenv('API_KEY')

# Check if the API key is available
if api_key is None:
    print("API key not found. Make sure it's defined in the .env file.")
    exit()

# Set up the request headers with the API key
headers = {
    'Authorization': f'Basic {api_key}',
    'AuthorizationSource': 'API'
}

# Set up the GraphQL variables
variables = {
}

# Set up the GraphQL endpoint URL
url = 'https://staging-api.gethealthie.com/graphql'

# Make the HTTP POST request to the Healthie API
response = requests.post(url, json={'query': query, 'variables': variables}, headers=headers)

# Check if the request was successful
# Handle the response as needed
if response.status_code == 200:
    # print(response.json())
    # Assuming response is the variable holding the JSON response
    response_data = response.json()

    # Pretty print the JSON response
    print(json.dumps(response_data, indent=4))
else:
    print("Error:", response.text)
