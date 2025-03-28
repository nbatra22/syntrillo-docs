import os
import requests
import unittest

# -----------------------------------------------------------------------------
# API Calls
# -----------------------------------------------------------------------------

def call_healthie_api_staging():
    # Base URL and parameters separated for clarity and security
    base_url = os.getenv('API_BASE_URL', 'https://api.staging.syntrillo-clinic-backend.com')
        
    headers = {
        'Referer': 'https://securestaging.gethealthie.com/'
    }

    path = '/iframe_healthie_provider_tab'
    
    # Make the GET request
    response = requests.get(
        f"{base_url}{path}",
        headers=headers,
        timeout=120
    )
    
    return response.status_code

# -----------------------------------------------------------------------------
# TESTS
# -----------------------------------------------------------------------------

class TestHealthieAPIStaging(unittest.TestCase):

    def test_successful_api_call_staging(self):
        
        # Call function
        result = call_healthie_api_staging()
        
        # Assertions
        self.assertEqual(result, 200)

if __name__ == '__main__':
    unittest.main()