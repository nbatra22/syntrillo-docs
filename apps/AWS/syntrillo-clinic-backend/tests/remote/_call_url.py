import os
import requests
from urllib.parse import urlencode

# -----------------------------------------------------------------------------
# API Calls
# -----------------------------------------------------------------------------

def call_healthie_api_staging():
    # Base URL and parameters separated for clarity and security
    base_url = os.getenv('API_BASE_URL', 'https://api.staging.syntrillo-clinic-backend.com')
    
    # Query parameters
    params = {
        'hl_current_user_id': '1173733',
        'referrer_url': 'https://securestaging.gethealthie.com/users/1525423'
    }
    
    # Construct the endpoint
    endpoint = '/iframe_healthie_provider_tab'
    
    # Make the GET request
    response = requests.get(
        f"{base_url}{endpoint}",
        params=params,
        timeout=120
    )
    
    return response.status_code

def call_healthie_api_prod():
    # Base URL and parameters separated for clarity and security
    base_url = os.getenv('API_BASE_URL', 'https://api.prod.syntrillo-clinic-backend.com')
    
    # Query parameters
    params = {
        'hl_current_user_id': '1173733',
        'referrer_url': 'https://securestaging.gethealthie.com/users/1525423'
    }
    
    # Construct the endpoint
    endpoint = '/iframe_healthie_provider_tab'
    
    # Make the GET request
    response = requests.get(
        f"{base_url}{endpoint}",
        params=params,
        timeout=120
    )
    
    return response.status_code

# -----------------------------------------------------------------------------
# TESTS
# -----------------------------------------------------------------------------

import unittest
import requests

class TestHealthieAPIStaging(unittest.TestCase):

    def test_successful_api_call_staging(self):
        
        # Call function
        result = call_healthie_api_staging()
        
        # Assertions
        self.assertEqual(result, 200)


class TestHealthieAPIProd(unittest.TestCase):

    def test_successful_api_call_prod(self):
        
        # Call function
        result = call_healthie_api_prod()
        
        # Assertions
        self.assertEqual(result, 200)

if __name__ == '__main__':
    unittest.main()