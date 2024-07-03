def handler(event, context):
    pass

if __name__ == '__main__':
    import unittest

    class TestFoundation(unittest.TestCase):
        def test_handler(self):
            self.assertEqual(None, handler(None, None))

    unittest.main()