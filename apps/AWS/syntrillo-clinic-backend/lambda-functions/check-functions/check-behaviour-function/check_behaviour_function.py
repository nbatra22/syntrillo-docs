import sys
import os

modules_to_control=["requests", "pandas", "plotly", "kaleido"]
import requests
import pandas
import plotly
import kaleido 
# N.B. When kaleido is installed via cloud9, the instance must have a minimum of 2GB ram (t3.small) 
# otherwise /tmp is too small for pip to install

# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------

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

    if resource_path == "/check_python_module_import":
        modules=[]
        for module in modules_to_control:
            if module in sys.modules.keys(): 
                modules.append(module)
            else:
                return response_500(f'[{module}]' + " module not present")

        return response_200(str(modules))

    return response_500()

# -----------------------------------------------------------------------------
# LOCAL TESTS
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import unittest

    class CheckBehaviour(unittest.TestCase):

        def test_no_check_selected(self):
            # "CHECK HAS NO RETURN" means the resource path is right but there is no return instruction
            expected = {
                'statusCode': 500,
                'body': 'NO CHECK SELECTED OR CHECK DOES NOT EXIST OR CHECK HAS NO RETURN'
            }
            self.assertEqual(expected, handler({"path": "/"}, None))

        def test_check_python_module_import(self):
            expected = {
                'statusCode': 200,
                'body': str(modules_to_control)
            }
            self.assertEqual(expected, handler({"path": "/check_python_module_import"}, None))

    unittest.main(verbosity=2)