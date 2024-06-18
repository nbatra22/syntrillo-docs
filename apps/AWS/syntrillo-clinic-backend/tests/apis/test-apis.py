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

iframe_generator_api_id = get_api_id('IFramGeneratorAPI')
landing_page_api_id = get_api_id('LandingPageAPI')

class TestSyntrilloClinicBackendAPIs(unittest.TestCase):

    def test_landing_page(self):
        url = f'https://{landing_page_api_id}.execute-api.us-east-1.amazonaws.com/prod/'
        status_code = requests.get(url).status_code
        self.assertEqual(status_code, 200, url)

    def test_flask_playground(self):
        url = f'https://{iframe_generator_api_id}.execute-api.us-east-1.amazonaws.com/prod/'
        status_code = requests.get(url).status_code
        self.assertEqual(status_code, 200, url)

    def test_iframe_healthie_provider_tab(self):
        url = f'https://{iframe_generator_api_id}.execute-api.us-east-1.amazonaws.com/prod/iframe_healthie_provider_tab'
        status_code = requests.get(url).status_code
        self.assertEqual(status_code, 200, url)

    def test_iframe_healthie_provider_tab_devices(self):
        url = f'https://{iframe_generator_api_id}.execute-api.us-east-1.amazonaws.com/prod/healthie/iframe_provider_tab/devices'
        device_form_data = {
            'healthie_provider_id': '1173733',
            'healthie_user_id': 'Not+transmitted',
            'temporary_lookup_code': '16823a6c-9ad0-4cbb-b5bb-498fa324287c',
            'patient_not_registered_at_syntrillo': 'False'
        }
        status_code = requests.post(url, data=device_form_data).status_code
        self.assertEqual(status_code, 200, url)

    def test_iframe_healthie_provider_tab_devices_generate_temporary_pairing_code(self):
        url = f'https://{iframe_generator_api_id}.execute-api.us-east-1.amazonaws.com/prod/healthie/iframe_provider_tab/devices/tenovi_generate_temporary_pairing_code_form'
        device_form_data = {
            'temporary_lookup_code': '69c70ff8-6589-42b2-8b54-1501079441e2',
        }
        status_code = requests.post(url, data=device_form_data).status_code
        self.assertEqual(status_code, 200, url)

    def test_iframe_healthie_provider_tab_devices_pair_devices(self):
        url = f'https://{iframe_generator_api_id}.execute-api.us-east-1.amazonaws.com/prod/healthie/iframe_provider_tab/devices/tenovi_pair_devices_form'
        device_form_data = {
            'temporary_lookup_code': '907c7bef-8295-470f-96b4-bb2e934a7750',
        }
        status_code = requests.post(url, data=device_form_data).status_code
        self.assertEqual(status_code, 200, url)

if __name__ == '__main__':
    unittest.main()

