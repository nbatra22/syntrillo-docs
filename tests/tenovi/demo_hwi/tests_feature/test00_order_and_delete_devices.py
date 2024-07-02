
import uuid
import random

from syntrillo.api_tenovi.devices import Devices

"""
This test will make actual API requests to create a set of devices.

The outcome can be seen on the Tenovi portal dashboard un der 'Delivered' devices :
   https://app.tenovi.com/client/devices?currentTab=Delivered

"""

devices_module = Devices()

random_patient_id = "delete_me-test-" + str(random.randint(100000, 999999))
random_patient_name = "Test Patient " + random_patient_id

created_devices, log = devices_module.create_set_of_devices_with_fulfillment_request(
    devices_names = ('Tenovi BPM - L', 'Tenovi Watch', 'Tenovi Pillbox'),
    patient_id = random_patient_id,
    pseudo_code_for_tenovi_phi_access__uuid = uuid.uuid4(),
    patient_name = random_patient_name,
    gateway_id = "0000-0000-0000",
    fullfillment_request=False,
)

devices_module.auth.print_pretty_json(log)

if log['success']:
    devices_module.auth.print_pretty_json(created_devices)

    print('\n\nDevices created successfully\n\n')

    # list the ids of the created devices
    for device in created_devices:
        device_id = device['id']
        device_name = device['device']['name']
        print(device_name.ljust(20), device_id)

    # prompt the user to check the Tenovi portal dashboard
    print(f"\nCheck the Tenovi portal dashboard for the devices created for {random_patient_name} with id {random_patient_id}")

    # delete the devices. ask confirmation everytime with the device id
    for device in created_devices:
        device_id = device['id']
        device_name = device['device']['name']
        if input(f"\nDelete device {device_name} with id {device_id}? (y/n) ").lower() == 'y':
            response, log = devices_module.delete_device(device_id)
            if log['success']:
                print(f"Device {device_name} with id {device_id} deleted successfully")
            else:
                devices_module.auth.print_pretty_json(log)


