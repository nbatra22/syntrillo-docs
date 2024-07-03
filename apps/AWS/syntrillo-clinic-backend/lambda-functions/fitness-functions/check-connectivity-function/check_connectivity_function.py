import requests

def test_internet_egress():
    response = requests.get("https://www.example.com")
    return str(response)

def response_200(message='Hello World'):
    return {
        'statusCode': 200,
        'body': message
    }

def response_500(message='Hello World'):
    return {
        'statusCode': 500,
        'body': message
    }

def handler(event, context):
    resource_path = event['path']

    if resource_path == "/test_internet_egress":
        response = test_internet_egress()
        if response == '<Response [200]>':
            return response_200('test_internet_egress ok')
        else:
            return response_500("Access to internet not available")

    return response_200()

if __name__ == '__main__':
    import unittest

    class TestFoundation(unittest.TestCase):
        
        def test_internet_ingress(self):
            expected = {
                'statusCode': 200,
                'body': 'Hello World'
            }
            self.assertEqual(expected, handler({"path": "/"}, None))

        def test_internet_egress(self):
            expected = {
                'statusCode': 200,
                'body': 'test_internet_egress ok'
            }
            self.assertEqual(expected, handler({"path": "/test_internet_egress"}, None))

    unittest.main()