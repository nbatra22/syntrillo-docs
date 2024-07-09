import requests
import sys
import os

sys.path.append('/mnt/python_modules')

# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------

from syntrillo.system.dot_env_loader import DotEnvFileLoader

from syntrillo.databases_management.connection import DatabaseConnection


class Database:
    def __init__(self):
        pass

    def get_connection(self):
        db_conn = DatabaseConnection(DatabaseConnection.PSEUDONYM_DB)
        self.conn, self.tunnel = db_conn.create_connection(verbose=True)
        return self.conn
    
    def close_connection(self):
        self.conn.close()

def call_public_url(url="https://www.example.com", headers='', params='{}'):
    response = requests.get(url, headers=headers, params=params)
    return response.status_code, response.text

def response_200(message='Hello World'):
    return {
        'statusCode': 200,
        'body': message
    }

def response_500(message='NO CHECK SELECTED OR CHECK DOES NOT EXIST OR CHECK HAS NO RETURN'):
    return {
        'statusCode': 500,
        'body': message
    }

# -----------------------------------------------------------------------------
# TEST ROUTER
# -----------------------------------------------------------------------------
def handler(event, context):
    resource_path = event['path']

    if resource_path == "/check_internet_ingress":
        return response_200('check_internet_ingress ok')
    
    if resource_path == "/check_internet_egress":
        status_code, text = call_public_url()
        if status_code == 200:
            return response_200('check_internet_egress ok')
        else:
            return response_500("check_internet_egress fail [No internet connection available]")

    if resource_path == "/check_api_url_access":
        status_code, text = call_public_url('https://api.sandbox.syntrillo-clinic-backend.com/')
        if status_code == 200:
            return response_200('check_api_url_access ok')
        else:
            return response_500("check_api_url_access fail [" + text + ']')

    if resource_path == "/check_tenovi_non_hwi_access":
        _ = DotEnvFileLoader()
        api_key=os.getenv('TENOVI_API_KEY_NON_HWI')
        client_domain=os.getenv('TENOVI_CLIENT_DOMAIN_NON_HWI')
        headers={'Authorization': f'Api-Key {api_key}', 'Content-Type': 'application/json'}
        status_code, text = call_public_url(f'https://api2.tenovi.com/clients/{client_domain}///hwi/hwi-devices/', headers)
        if status_code == 200:
            return response_200('check_tenovi_non_hwi_access ok')
        else:
            return response_500("check_tenovi_non_hwi_access fail [" + text + ']')

    if resource_path == "/check_tenovi_hwi_access":
        _ = DotEnvFileLoader()
        api_key=os.getenv('TENOVI_API_KEY_HWI')
        client_domain=os.getenv('TENOVI_CLIENT_DOMAIN_HWI')
        headers={'Authorization': f'Api-Key {api_key}', 'Content-Type': 'application/json'}
        status_code, text = call_public_url(f'https://api2.tenovi.com/clients/{client_domain}///hwi/hwi-devices/', headers)
        if status_code == 200:
            return response_200('check_tenovi_hwi_access ok')
        else:
            return response_500("check_tenovi_hwi_access fail [" + text + ']')

    if resource_path == "/check_mysql_database_access":
        db = Database()
        connection = db.get_connection()
        if connection:
            db.close_connection()
            return response_200('check_mysql_database_access ok')
        else:
            return response_500('check_mysql_database_access fail')

    return response_500()

# -----------------------------------------------------------------------------
# LOCAL TESTS
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import unittest

    class CheckFoundations(unittest.TestCase):
        
        def test_no_check_selected(self):
            # "CHECK HAS NO RETURN" means the resource path is right but there is no return instruction
            expected = {
                'statusCode': 500,
                'body': 'NO CHECK SELECTED OR CHECK DOES NOT EXIST OR CHECK HAS NO RETURN'
            }
            self.assertEqual(expected, handler({"path": "/"}, None))
        
        def test_check_internet_ingress(self):
            expected = {
                'statusCode': 200,
                'body': 'check_internet_ingress ok'
            }
            self.assertEqual(expected, handler({"path": "/check_internet_ingress"}, None))

        def test_check_internet_egress(self):
            expected = {
                'statusCode': 200,
                'body': 'check_internet_egress ok'
            }
            self.assertEqual(expected, handler({"path": "/check_internet_egress"}, None))

        def test_check_mysql_database_access(self):
            expected = {
                'statusCode': 200,
                'body': 'check_mysql_database_access ok'
            }
            self.assertEqual(expected, handler({"path": "/check_mysql_database_access"}, None))
        
        # def test_check_api_url_access(self):
        #     expected = {
        #         'statusCode': 200,
        #         'body': 'check_api_url_access ok'
        #     }
        #     self.assertEqual(expected, handler({"path": "/check_api_url_access"}, None))        

        def test_check_tenovi_non_hwi_access(self):
            expected = {
                'statusCode': 200,
                'body': 'check_tenovi_non_hwi_access ok'
            }
            self.assertEqual(expected, handler({"path": "/check_tenovi_non_hwi_access"}, None))

        def test_check_tenovi_hwi_access(self):
            expected = {
                'statusCode': 200,
                'body': 'check_tenovi_hwi_access ok'
            }
            self.assertEqual(expected, handler({"path": "/check_tenovi_hwi_access"}, None))

    unittest.main()