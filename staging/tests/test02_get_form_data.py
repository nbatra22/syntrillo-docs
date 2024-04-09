# using conda 'syntrillo' environment

# query from https://docs.gethealthie.com/docs/#querying-filled-out-forms
# use https://docs.gethealthie.com/docs/explorer to get parameters

import requests
import os
import json
from dotenv import load_dotenv

# Set up the GraphQL query
query = '''
query formAnswerGroups(
  $date: String,
  $custom_module_form_id: ID,
  $user_id: String,
  ) {
  formAnswerGroups(
    date: $date,
    custom_module_form_id: $custom_module_form_id,
    user_id: $user_id,
    ) {
    id
    name
    created_at
    user_id
    finished
    form_answers {
      custom_module_id
      label
      answer
      # id
    }
  }
}
'''

# Load environment variables from .env file
dotenv_path = os.path.abspath(os.path.dirname(os.path.abspath(sys.argv[0])) + "/../.env")
load_dotenv(dotenv_path=dotenv_path)

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
    # 'date': "2021-10-29",  # Example date value
    # 'custom_module_form_id': "11",  # Example custom_module_form_id value
    'user_id' : '1035117'
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
