import requests
import unittest

class TestFoundation(unittest.TestCase):

    # 502 Http Error means the lambda function is not working properly (it returns None for example or it is timedout)
    # N.B. Keep in mind that lambda time out includes cold start 
    # (i.e. if the timeout is 3s and the lambda function take 3 seconds to start it will timeout), 
    # you should then increase the lambda timeout in the cdk stack
    
    # def test_static(self):
    #     url = f'https://athdqpk08c.execute-api.us-east-1.amazonaws.com/sandbox/static/healthie.css'
    #     request = requests.get(url)
    #     status_code = request.status_code
    #     self.assertEqual(status_code, 200)

    # def test_direct_url(self):
    #     url = f'https://api.staging.syntrillo-clinic-backend.com/iframe_healthie_provider_tab'
    #     request = requests.get(url)
    #     status_code = request.status_code
    #     self.assertEqual(status_code, 200)

    # def test_api_url(self):
    #     url = f'https://nh449amm35.execute-api.us-east-1.amazonaws.com/staging/iframe_healthie_client_sidebar'
    #     request = requests.get(url)
    #     status_code = request.status_code
    #     self.assertEqual(status_code, 200)

    def test_staging_iframe_provider_tab(self):
        url = f'https://api.staging.syntrillo-clinic-backend.com/iframe_healthie_provider_tab'

        # Define the headers you want to add
        headers = {
            "referer": "https://patients.syntrillo.com/",
        }

        request = requests.get(url, headers=headers)
        status_code = request.status_code
        self.assertEqual(status_code, 200)

    def test_staging_get_blood_pressure_plot(self):
        url = f'https://api.staging.syntrillo-clinic-backend.com/healthie/iframe_provider_tab/care_plan/get_blood_pressure_plot'

        # Define the headers you want to add
        headers = {
            "referer": "https://patients.syntrillo.com/",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        }

        data = "temporary_lookup_code=e6f2dd27-cd35-4afd-b554-863ab685d4b0&json_or_html=json"
        request = requests.post(url, data=data, headers=headers)
        status_code = request.status_code
        self.assertEqual(status_code, 200)

    def test_prod_iframe_provider_tab(self):
        url = f'https://api.prod.syntrillo-clinic-backend.com/iframe_healthie_provider_tab'

        # Define the headers you want to add
        headers = {
            "referer": "https://patients.syntrillo.com/",
        }

        request = requests.get(url, headers=headers)
        status_code = request.status_code
        self.assertEqual(status_code, 200)

    def test_prod_get_blood_pressure_plot(self):
        url = f'https://api.prod.syntrillo-clinic-backend.com/healthie/iframe_provider_tab/care_plan/get_blood_pressure_plot'

        # Define the headers you want to add
        headers = {
            "referer": "https://patients.syntrillo.com/",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        }

        data = "temporary_lookup_code=e6f2dd27-cd35-4afd-b554-863ab685d4b0&json_or_html=json"
        request = requests.post(url, data=data, headers=headers)
        status_code = request.status_code
        self.assertEqual(status_code, 200)

if __name__ == '__main__':
    unittest.main(verbosity=2)
