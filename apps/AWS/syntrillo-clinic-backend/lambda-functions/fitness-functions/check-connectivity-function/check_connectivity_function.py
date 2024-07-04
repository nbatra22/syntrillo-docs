import requests
import sys

sys.path.append('/mnt/python_modules')

modules_to_control=["pandas", "plotly", "kaleido"]
import pandas
import plotly
import kaleido 
# N.B. When kaleido is installed via cloud9, the instance must have a minimum of 2GB ram (t3.small) 
# otherwise /tmp is too small for pip to install

# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------

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

def test_internet_egress():
    response = requests.get("https://www.example.com")
    return str(response)

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

    if resource_path == "/check_internet_egress":
        response = test_internet_egress()
        if response == '<Response [200]>':
            return response_200('check_internet_egress ok')
        else:
            return response_500("check_internet_egress fail [No internet connection available]")
    
    if resource_path == "/check_internet_ingress":
        return response_200('check_internet_ingress ok')

    if resource_path == "/check_python_module_import":
        modules=[]
        for module in modules_to_control:
            if module in sys.modules.keys(): 
                modules.append(module)
            else:
                return response_500(module + " module not present")

        return response_200(str(modules))

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

        def test_check_python_module_import(self):
            expected = {
                'statusCode': 200,
                'body': str(modules_to_control)
            }
            self.assertEqual(expected, handler({"path": "/check_python_module_import"}, None))

    unittest.main()