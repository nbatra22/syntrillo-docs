import requests
import unittest

import boto3

def get_api_id(api_name):
    api_gateway = boto3.client('apigateway')
    apis = api_gateway.get_rest_apis()
    
    for api in apis['items']:
        if api['name'] == api_name:
            return api['id']
    
    print(f"API '{api_name}' not found.")
    return None

check_connectivity_api_id = get_api_id('CheckConnectivityAPI')
# iframe_generator_api_id = get_api_id('IFramGeneratorAPI')
# landing_page_api_id = get_api_id('LandingPageAPI')

from datetime import datetime, timedelta
import time

def display_error_context(url, request):
    error_context = "\n" + (">"*80)
    error_context += f"\nURL: {url}"
    error_context += f"\nRESPONSE: {request.text}"
    error_context += "\n" + ("<"*80)

    return error_context

    if (request.status_code==200):
        return error_context
    # 
    logs = boto3.client('logs')

    # Describe the log streams in the log group
    response = logs.describe_log_streams(
        logGroupName="/aws/lambda/CheckingFunction",
        orderBy='LastEventTime',
        descending=True,
        limit=1
    )

    logstream_name = response['logStreams'][0]['logStreamName']

    # Get the start and end times for the last 1 minute
    end_time = datetime.now()
    start_time = end_time - timedelta(seconds=10)

    time.sleep(10)

    # Retrieve the log events
    response = logs.get_log_events(
        logGroupName="/aws/lambda/CheckingFunction",
        logStreamName=logstream_name,
        startTime=int(start_time.timestamp() * 1000),
        endTime=int(end_time.timestamp() * 1000),
        limit=10,
        startFromHead=False
    )

    for event in response['events']:
        error_context +=  str(event['timestamp']) + ":" + event['message']

    error_context += "\n" + ("<"*80)
    return error_context

class TestFoundation(unittest.TestCase):

    def test_check_connectivity_function_internet_ingress(self):
        url = f'https://{check_connectivity_api_id}.execute-api.us-east-1.amazonaws.com/sandbox/'
        request = requests.get(url)
        status_code = request.status_code
        self.assertEqual(status_code, 200, display_error_context(url, request))
        # 502 means the lambda function is not working properly (it returns None for example or it is timedout)
        # N.B. Keep in mind that lambda time out includes cold start 
        # (i.e. if the timeout is 3s and the lambda function take 3 seconds to start it will timeout), 
        # you should then increase the lambda timeout in the cdk stack
    
    def test_check_connectivity_function_internet_egress(self):
        url = f'https://{check_connectivity_api_id}.execute-api.us-east-1.amazonaws.com/sandbox/'
        url += 'test_internet_egress'
        request = requests.get(url)
        status_code = request.status_code
        self.assertEqual(status_code, 200, display_error_context(url, request))

    # def test_tenovi_access(self):
    #     url = f'https://{check_connectivity_api_id}.execute-api.us-east-1.amazonaws.com/sandbox/'
    #     url += 'test_tenovi_access'
    #     request = requests.get(url)
    #     status_code = request.status_code
    #     self.assertEqual(status_code, 200, display_error_context(url, request))

    # def test_database_access(self):
    #     url = f'https://{check_connectivity_api_id}.execute-api.us-east-1.amazonaws.com/sandbox/'
    #     url += 'test_database_access'
    #     request = requests.get(url)
    #     status_code = request.status_code
    #     self.assertEqual(status_code, 200, display_error_context(url, request))

# class TestProcesses(unittest.TestCase):
    
#     def test_register_patient_devices(self):
#         url = f'https://{check_connectivity_api_id}.execute-api.us-east-1.amazonaws.com/sandbox/'
#         url += 'register_patient_devices'
#         request = requests.get(url)
#         status_code = request.status_code
#         self.assertEqual(status_code, 200, display_error_context(url, request))

# class TestFlaskLandingPage(unittest.TestCase):

#     def test_landing_page(self):
#         url = f'https://{landing_page_api_id}.execute-api.us-east-1.amazonaws.com/sandbox/'
#         request = requests.get(url)
#         status_code = request.status_code
#         self.assertEqual(status_code, 200, display_error_context(url, request))

if __name__ == '__main__':
    unittest.main(verbosity=2)

