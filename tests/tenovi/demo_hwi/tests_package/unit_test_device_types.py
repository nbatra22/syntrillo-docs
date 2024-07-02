import unittest
from unittest.mock import patch, MagicMock
from syntrillo.api_tenovi.device_types import DeviceTypes

class TestDeviceTypes(unittest.TestCase):
    @patch('syntrillo.api_tenovi.device_types.TenoviAuth')
    def test_get_device_types(self, MockTenoviAuth):
        # Create a mock instance of TenoviAuth
        mock_auth_instance = MockTenoviAuth.return_value

        # Define the mock return value for make_get_request
        mock_response = (
            [
                {"name": "Tenovi BPM - L", "id": "7ffa3c62-cb7b-48e6-8904-f480cf674b1a"},
                {"name": "Tenovi BPM - S", "id": "fd0aa442-833c-4ae7-8d2f-4b532c275f71"},
                {"name": "Tenovi Watch", "id": "c3b8e140-7791-4859-83fd-3704bcb3ef7c"},
                {"name": "Tenovi Pillbox", "id": "6b6d3d3e-e979-474e-b0cb-c114d11299f5"},
            ],
            {"success": True, "message": "Successfully posted data in get_device_types"}
        )
        mock_auth_instance.make_get_request.return_value = mock_response

        # Create an instance of DeviceTypes
        device_types_instance = DeviceTypes()

        # Call the method to be tested
        device_types, log = device_types_instance.get_device_types()

        # Assertions to check if the method behaves as expected
        self.assertEqual(device_types, mock_response[0])
        self.assertEqual(log, mock_response[1])
        self.assertTrue(log['success'])


if __name__ == '__main__':
    unittest.main()
