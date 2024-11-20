import os
import requests
import json

import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name, region_name="us-east-1"):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        # Retrieve the secret
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # Handle potential errors
        raise e
    else:
        # If no error, return the secret
        if 'SecretString' in get_secret_value_response:
            return get_secret_value_response['SecretString']
        else:
            return get_secret_value_response['SecretBinary']

# Usage
secret_name = "TenoviHWISecrets1DCFD16F-cynGGcooiiAq"
try:
    secret = json.loads(get_secret(secret_name))
    print(f"Retrieved secret: {secret}")
except Exception as e:
    print(f"Error retrieving secret: {str(e)}")

# Fetch API keys from environment variables
API_KEY_HWI = secret['tenoviHwiApiKey']
CLIENT_DOMAIN_HWI = secret['tenoviHwiClientDomain']

# Use non-HWI credentials
API_KEY = API_KEY_HWI
CLIENT_DOMAIN = CLIENT_DOMAIN_HWI

headers = {
    "Authorization": f"Api-Key {API_KEY}",
    "Content-Type": "application/json"
}

# First request
print("##### FIRST REQUEST #####")
pseudo_code_for_tenovi_phi_access = '4c3df78d-2a17-4ed7-9a6a-2cccd94abca0'
base_url = f"https://api2.tenovi.com/clients/{CLIENT_DOMAIN}/hwi/hwi-devices/"
params={'properties__key': 'pseudo_code_for_tenovi_phi_access', 'properties__value': pseudo_code_for_tenovi_phi_access}

response = requests.get(base_url, headers=headers, params=params)
if response.status_code == 200:
    for device in response.json():
        print(device['id'])
    # print(response.json()[0]['device']['id'])
    # print(json.dumps(response.json(), indent=2))
else:
    print(f"Error: {response.status_code}")

print("##### SECOND REQUEST #####")
hwi_device_id='e9c24a26-7d69-490f-9546-93c5a31486aa'
base_url = f"https://api2.tenovi.com/clients/{CLIENT_DOMAIN}/hwi/hwi-devices/{hwi_device_id}/measurements/"
params={'created__gte': '2024-09-10T14:19:32.202863Z', 'created__lte': '2024-10-07T09:43:46.510493Z'}

response = requests.get(base_url, headers=headers, params=params)
if response.status_code == 200:
    for measurement in response.json():
        print(measurement['timezone_offset'])
    # print(json.dumps(response.json(), indent=2))
else:
    print(f"Error: {response.status_code}")