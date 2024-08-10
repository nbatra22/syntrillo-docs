# Path: ./tests/tenovi/demo_hwi/tests_package/unit_test_order_and_delete_devices.py
import unittest
import uuid
import random
import time

from syntrillo.api_tenovi.devices import Devices

class TestDevices(unittest.TestCase):
    """
    This class contains unit tests for some functions of the Devices class.

    This class is making actual API requests to the Tenovi API to create and delete devices.

    """
    def setUp(self):
        self.devices_module = Devices()
        self.random_patient_id = "delete_me-test-" + str(random.randint(100000, 999999))
        self.random_patient_name = "Test Patient " + self.random_patient_id

    def test_create_and_delete_devices(self):

        print("\nCreating the devices...")

        # Create devices
        created_devices, log = self.devices_module.create_set_of_devices_with_fulfillment_request(
            devices_names=('Tenovi BPM - L', 'Tenovi Watch', 'Tenovi Pillbox'),
            patient_id=self.random_patient_id,
            pseudo_code_for_tenovi_phi_access__uuid=uuid.uuid4(),
            patient_name=self.random_patient_name,
            gateway_id="0000-0000-0000",
            fullfillment_request=False,
        )

        self.assertTrue(log['success'], "Failed to create devices")

        if log['success']:

            print('\nDevices created successfully\n')

            # List the ids of the created devices
            for device in created_devices:
                device_id = device['id']
                device_name = device['device']['name']
                print(device_name.ljust(20), device_id)


            print("\nDeleting the devices...\n")

            time.sleep(5)

            # Delete the devices
            for device in created_devices:
                device_id = device['id']
                device_name = device['device']['name']
                response, log = self.devices_module.delete_device(device_id)
                self.assertTrue(log['success'], f"Failed to delete device {device_name} with id {device_id}")
                if log['success']:
                    print(f"Device {device_name.ljust(20)} with id {device_id} deleted successfully")
                else:
                    self.devices_module.auth.print_pretty_json(log)

if __name__ == '__main__':
    if input(f"\n\nConfirm we are in a DEMO TENOVI ENVIRONMENT (y/n) : ").lower() == 'y':
        unittest.main()

