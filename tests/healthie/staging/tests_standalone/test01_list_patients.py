# ./Syntrillo_Clinic/tests/healthie/staging/tests_standalone/test01_list_patients.py

# using conda 'syntrillo' environment

# query from https://docs.gethealthie.com/docs/#list-all-patients

import requests
import os
from dotenv import load_dotenv

# Set up the GraphQL query
query = '''
query users(
  $offset: Int,
  $keywords: String,
  $sort_by: String,
  $active_status: String,
  $group_id: String,
  $show_all_by_default: Boolean,
  $should_paginate: Boolean,
  $provider_id: String,
  $conversation_id: ID,
  $limited_to_provider: Boolean,
) {
  usersCount(
    keywords: $keywords,
    active_status:$active_status,
    group_id: $group_id,
    conversation_id: $conversation_id,
    provider_id: $provider_id,
    limited_to_provider: $limited_to_provider
  )
  users(
    offset: $offset,
    keywords: $keywords,
    sort_by: $sort_by,
    active_status: $active_status,
    group_id: $group_id,
    conversation_id: $conversation_id,
    show_all_by_default: $show_all_by_default,
    should_paginate: $should_paginate,
    provider_id: $provider_id,
    limited_to_provider: $limited_to_provider
  ) {
      id
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
    'offset': 0,  # Offset for pagination (if applicable)
    # Add other variables as needed
}

# Set up the GraphQL endpoint URL
url = 'https://staging-api.gethealthie.com/graphql'

# Make the HTTP POST request to the Healthie API
response = requests.post(url, json={'query': query, 'variables': variables}, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    data = response.json()
    # Extract the list of patient IDs from the response
    patient_ids = [user['id'] for user in data['data']['users']]
    print("List of patient IDs:", patient_ids)
else:
    print("Failed to retrieve patient list. Status code:", response.status_code)


