import requests
import sys

modules_to_control=["pandas"]
import pandas

def test_internet_egress():
    response = requests.get("https://www.example.com")
    return str(response)

def response_200(message='Hello World'):
    return {
        'statusCode': 200,
        'body': message
    }

def response_500(message='NO CHECK SELECTED OR CHECK DOES NOT EXIST'):
    return {
        'statusCode': 500,
        'body': message
    }

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

        return response_200(modules)

    return response_500()

if __name__ == '__main__':
    import unittest

    class CheckFoundations(unittest.TestCase):
        
        def test_no_check_selected(self):
            expected = {
                'statusCode': 500,
                'body': 'NO CHECK SELECTED OR CHECK DOES NOT EXIST'
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

        def test_check_python_module_import(self):
            expected = {
                'statusCode': 200,
                'body': modules_to_control
            }
            self.assertEqual(expected, handler({"path": "/check_python_module_import"}, None))

    unittest.main()