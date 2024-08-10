# Path: ./tests/tenovi/demo_hwi/tests_package/unit_test_device_types.py
import unittest
from unittest.mock import patch
from syntrillo.api_tenovi.device_types import DeviceTypes

class TestDeviceTypes(unittest.TestCase):
    """
    This class contains unit tests for the DeviceTypes class.

    This class is making actual API requests to the Tenovi API to retrieve device types.

    """
    @patch('syntrillo.api_tenovi.device_types.TenoviAuth.make_get_request')
    def test_get_device_types(self, mock_make_get_request):
        # Arrange
        expected_device_types = [
            {"name": "Tenovi BPM - L", "id": "7ffa3c62-cb7b-48e6-8904-f480cf674b1a"},
            {"name": "Tenovi BPM - S", "id": "fd0aa442-833c-4ae7-8d2f-4b532c275f71"},
            {"name": "Tenovi Watch", "id": "c3b8e140-7791-4859-83fd-3704bcb3ef7c"},
            {"name": "Tenovi Pillbox", "id": "6b6d3d3e-e979-474e-b0cb-c114d11299f5"}
        ]
        expected_log = {'success': True, 'message': 'Successfully posted data in get_device_types'}
        mock_make_get_request.return_value = (expected_device_types, expected_log)

        # Act
        device_types_module = DeviceTypes()
        device_types, log = device_types_module.get_device_types()

        # Assert
        self.assertEqual(device_types, expected_device_types)
        self.assertEqual(log, expected_log)
        mock_make_get_request.assert_called_once_with("/hwi/hwi-device-types/")

if __name__ == '__main__':
    unittest.main()

