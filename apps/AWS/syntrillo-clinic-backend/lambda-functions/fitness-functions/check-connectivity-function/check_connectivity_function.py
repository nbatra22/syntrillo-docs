def handler(event, context):
    return {
        'statusCode': 200,
        'body': 'Hello World'
    }

if __name__ == '__main__':
    import unittest

    class TestFoundation(unittest.TestCase):
        def test_handler(self):
            expected = {
                'statusCode': 200,
                'body': 'Hello World'
            }
            self.assertEqual(expected, handler(None, None))

    unittest.main()