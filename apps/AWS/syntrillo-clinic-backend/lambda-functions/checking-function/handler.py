import json
import requests

def call_example_dot_com_url():
    response = requests.get("https://www.example.com")
    print(response.text)

def handler(event, context):
    print(event)

    resource_path = event['path']
    print(f"Resource path: {resource_path}")

    if resource_path == "/test_network_outside_connectivity":
        call_example_dot_com_url()
        return {
            'statusCode': 200,
            'body': 'Called example.com'
        }

    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!'
    }