import requests
import unittest

class TestFoundation(unittest.TestCase):

    # 502 Http Error means the lambda function is not working properly (it returns None for example or it is timedout)
    # N.B. Keep in mind that lambda time out includes cold start 
    # (i.e. if the timeout is 3s and the lambda function take 3 seconds to start it will timeout), 
    # you should then increase the lambda timeout in the cdk stack
    
    def test_check_connectivity_function_returns_error_if_no_check_selected(self):
        url = f'https://athdqpk08c.execute-api.us-east-1.amazonaws.com/sandbox/static/healthie.css'
        request = requests.get(url)
        status_code = request.status_code
        self.assertEqual(status_code, 200)


if __name__ == '__main__':
    unittest.main(verbosity=2)