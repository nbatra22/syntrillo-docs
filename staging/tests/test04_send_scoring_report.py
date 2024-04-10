# test to send freetext to a scoring report template

# looks like the answer can include html : "form_answers": [ {"label": "report", "answer": "<p>some data here</p>" } ]

import requests
import os
import json
import sys
from dotenv import load_dotenv


# hardcoding outputs for this test
ChartFormID='1138192'  # how to get this number programatically? I got it from the URL when creating the chart form.
CustomModuleID='9814779' # how do I get this number programatically ?
UserID='1035117'

# Define the HTML content for testing
html_content = '''
<!DOCTYPE html>
<html>
<head>
    <title>HTML Content Test</title>
</head>
<body>
    <h1 style="color: blue;">Health Report</h1>
    <p>This is a test report containing:</p>
    <ul>
        <li>Some bullet points</li>
        <li>Table with colored cells</li>
    </ul>
    <table border="1">
        <tr>
            <td style="background-color: lightgreen;">Cell 1</td>
            <td style="background-color: lightblue;">Cell 2</td>
        </tr>
        <tr>
            <td style="background-color: lightcoral;">Cell 3</td>
            <td style="background-color: lightskyblue;">Cell 4</td>
        </tr>
    </table>
    <p>iFrame starts:</p>
    <iframe src="https://www.syntrillo.com" width="800" height="600" style="border: 1px solid #ccc;"></iframe>
    <p>iFrame ends</p>
</body>
</html>
'''

# Set up the GraphQL variables for the mutation
variables = {
    'finished': True,
    'custom_module_form_id': ChartFormID,
    'user_id': UserID,
    'form_answers': [
        {
            "custom_module_id": CustomModuleID,
            "label": "report",
            "answer": html_content,
            }
    ]
}

# Set up the GraphQL endpoint URL
url = 'https://staging-api.gethealthie.com/graphql'

# GraphQL mutation for creating a form answer group
mutation = '''
mutation createFormAnswerGroup(
  $finished: Boolean!,
  $custom_module_form_id: String!,
  $user_id: String!,
  $form_answers: [FormAnswerInput!]!
) {
  createFormAnswerGroup(
    input: {
      finished: $finished,
      custom_module_form_id: $custom_module_form_id,
      user_id: $user_id,
      form_answers: $form_answers,
    }
  ) {
    form_answer_group {
      id
    }
    messages {
      field
      message
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

# Make the HTTP POST request to the GraphQL endpoint
response = requests.post(url, json={'query': mutation, 'variables': variables}, headers=headers)

# Handle the response
if response.status_code == 200:
    # Pretty print the JSON response
    print(json.dumps(response.json(), indent=4))
else:
    print("Error:", response.text)




