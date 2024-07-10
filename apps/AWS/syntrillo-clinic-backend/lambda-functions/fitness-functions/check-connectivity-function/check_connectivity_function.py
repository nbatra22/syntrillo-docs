import requests
import sys
import os
import json

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
# HELPERS
# -----------------------------------------------------------------------------
import requests
import os
import json

def get_secrets(secret_arn):
    try:
        get_secret_value_response = requests.get(
            f"http://localhost:2773/secretsmanager/get?secretId={secret_arn}",
            headers={"X-AWS-Parameters-Secrets-Token": os.environ.get('AWS_SESSION_TOKEN')},
        )
        get_secret_value_response.raise_for_status()  # Raise an exception for non-2xx status codes
    except requests.exceptions.RequestException as e:
        # Handle exceptions related to the HTTP request
        # if "an unexpected error occurred while executing request" in the response text => check lammbda permissions to read in secrets manager
        raise Exception(f"Error fetching secret [{get_secret_value_response.text}]: {e}")

    try:
        secret_value = get_secret_value_response.text
        secret_dict = json.loads(secret_value)
    except json.JSONDecodeError as e:
        # Handle exceptions related to JSON decoding
        raise Exception(f"Error decoding secret value [{get_secret_value_response.text}]: {e}")

    try:
        secrets_string = secret_dict["SecretString"]
    except KeyError as e:
        # Handle exceptions related to missing "SecretString" key
        raise Exception(f"Error retrieving SecretString: {e}")
    
    try:
        secrets_dict=json.loads(secrets_string)
        return secrets_dict
    except json.JSONDecodeError as e:
        # Handle exceptions related to not well formated secret string (non json)
        raise Exception(f"Error decoding secrets (should be in json format in aws secrets manager): {e}")

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
        if os.getenv('AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN') != None:
            tenovi_hwi_secrets=get_secrets(os.getenv('AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN'))
            api_key=tenovi_hwi_secrets["tenoviHwiApiKey"]
            client_domain=tenovi_hwi_secrets["tenoviHwiClientDomain"]
        else:
            _ = DotEnvFileLoader()
            api_key=os.getenv('TENOVI_API_KEY_HWI')
            client_domain=os.getenv('TENOVI_CLIENT_DOMAIN_HWI')

        headers={'Authorization': f'Api-Key {api_key}', 'Content-Type': 'application/json'}
        status_code, text = call_public_url(f'https://api2.tenovi.com/clients/{client_domain}///hwi/hwi-devices/', headers)
        if status_code == 200:
            return response_200('check_tenovi_hwi_access ok')
        else:
            return response_500("check_tenovi_hwi_access fail [" f'https://api2.tenovi.com/clients/{client_domain}///hwi/hwi-devices/' + str(headers) + text + "]")

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

    unittest.main(verbosity=2)