import requests

def test_internet_egress():
    response = requests.get("https://www.example.com")
    return str(response)

def handler(event, context):
    resource_path = event['path']

    if resource_path == "/test_internet_egress":
        return test_internet_egress()

    return {
        'statusCode': 200,
        'body': 'Hello World'
    }

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
            expected = '<Response [200]>'
            self.assertEqual(expected, handler({"path": "/test_internet_egress"}, None))

    unittest.main()