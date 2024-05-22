# ./Syntrillo_Clinic/tests/healthie/staging/tests_standalone/test03_webhook.py

# https://docs.gethealthie.com/docs/#examples

# webhook : form_answer_group.created : When a Patient completes a Form (intake, program or charting)

# testing endpoint at PythonAnywhere

# the payload for form_answer_group.created is
#       {"resource_id": 390125, "resource_id_type": "FormAnswerGroup", "event_type": "form_answer_group.created"}
# where resource_id  is specific to the form and the patient. Same is as in test02 :
#        {
#            "data": {
#                "formAnswerGroups": [
#                    {
#                        "id": "390125",


import requests
import json

# Define the payload to be sent in the POST request
payload = {
    "event": "appointment_scheduled",
    "data": {
        "client_id": "123456",
        "appointment_date": "2024-04-05",
        "appointment_time": "10:00 AM",
        "provider_id": "789012"
    }
}

# Define the URL of your Flask application
url = 'https://syntrillo.pythonanywhere.com/endpoint'

# Send the POST request with the payload
response = requests.post(url, json=payload)

# Print the response from the server
print(response.status_code)
print(response.json())

