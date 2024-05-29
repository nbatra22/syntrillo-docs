# Path: ./sources/syntrillo/api_tenovi/devices.py

from syntrillo.api_tenovi.auth import TenoviAuth

class Devices:
    """
    Gives access to Tenovi devices

    Example of device data :

    {
        "device": {
            "created": "2024-05-23T20:51:29.211103Z",
            "fulfillment_request": null,
            "hardware_uuid": "C26B2B7D56DC412BBE89D302C52717A5",
            "id": "f22e0ce6-dd5c-4e38-ba45-aac59d8b985f",
            "meta_data": null,
            "name": "Tenovi Pulse Ox",
            "sensor_code": "11",
            "shared_hardware_uuid": false
        },
        "id": "83ca5817-0bb2-4d9c-b131-16eb353ad587",   => this is the 'Device ID' displayed on the Device Dashboard, and hwi_device_id in get_devices()
        "patient": {
            "care_manager": null,
            "clinic_name": null,
            "email": null,
            "external_id": "AnExternalID",      => this is the 'Patient ID' displayed on the Device Dashboard
            "name": "PatientOne",
            "phone_number": null,
            "physician": null,
            "sms_opt_in": true
        },
        "patient_id": "AnExternalID",       => this is the 'Patient ID' displayed on the Device Dashboard
        "patient_phone_number": null,
        "status": "Unknown Gateway ID"
    }

    "patient_id" == "patient"."external_id" == "patient__external_id" query parameter
        : is the 'Patient ID' displayed on the Device Dashboard
        : 'This is a user-provided ID that will be included with all Webhook data.'  TODO: Any or ID sent as well ???
        : 'You can re-use this ID with other Hwi Devices to link all associated patient info.'


    """
    def __init__(self, client_domain="syntrillo"):
        self.client_domain = client_domain
        self.auth = TenoviAuth()

    def get_devices(self, hwi_device_id  : str = None, **kwargs):
        """
        Lists all or reads a single HWI Device. To read a single HWI Device, the ID must be included in the URL.

        Query parameters:
            - device__hardware_uuid__iexact: string
            - device__hardware_uuid: string
            - patient__external_id: string
            - properties__key: string
            - properties__value: string
            - search: string

        https://api2.tenovi.com/hwi-redoc/#tag/hwi-devices
        """

        url = f"https://api2.tenovi.com/clients/{self.client_domain}/hwi/hwi-devices/"
        if hwi_device_id:
            url += f"{hwi_device_id}/"

        return self.auth.make_get_request(url, params=kwargs)

    def get_devices_by_patient_external_id(self, external_id):
        """
        Returns devices matching patient external ID
        """
        query_params = {
            "patient__external_id": external_id,
        }
        return self.get_devices(**query_params)

    def get_devices_by_pseudo_code(self, pseudo_code_for_tenovi_phi_access):
        """
        Returns devices matching the pseudo_code_for_tenovi_phi_access key/value propoerty
        """
        query_params = {
            "properties__key": "pseudo_code_for_tenovi_phi_access",
            "properties__value": pseudo_code_for_tenovi_phi_access,
        }
        return self.get_devices(**query_params)


    def create_device(self, payload : dict):
        """
        Creates a new HWI Device with optional Fulfillment Request

        A nested Device object is required. Within this object, the Device name must exactly match the name of a Device Type associated with your account. You may use the hwi-device-types endpoint to view a complete list of Device Types associated with your account.

        You can also optionally link this Device to a Patient by including a nested Patient object. If you do this, the "external_id" field can be used to uniquely identify this Patient. For example, if you edit the name or phone_number of a Patient, those fields will be updated for all Devices the same Patient external_id. We thus recommend Clients use a unique Patient identifier from their own systems for this field (hence the name "external_id").

        https://api2.tenovi.com/hwi-redoc/#tag/hwi-devices
        """
        url = f"https://api2.tenovi.com/clients/{self.client_domain}/hwi/hwi-devices/"
        return self.auth.make_post_request(url, payload)

    def update_device_patient_id(self, hwi_device_id : str, patient_id : str):
        """
        Updates the patient_id of a device.

        See https://api2.tenovi.com/hwi-redoc/#operation/hwi-devices_partial_update
        """
        url = f"https://api2.tenovi.com/clients/{self.client_domain}/hwi/hwi-devices/{hwi_device_id}/"
        payload = {
            "patient_id": patient_id,
        }
        return self.auth.make_patch_request(url, payload)


# Example usage:
if __name__ == "__main__":
    devices_module = Devices()

    # Get and print all devices or a specific device
    devices = devices_module.get_devices()
    if devices:
        print("Devices:")
        devices_module.auth.print_pretty_json(devices)
    else:
        print("Devices: None found.")

    if False:
        # Example HWI device ID, replace with a real ID if needed
        # hwi_device_id = "0585a82e-3f57-4e0e-a91a-317117c48e11"
        hwi_device_id = "beb8e7cc-e8fe-4c8c-a273-bc54ac4bf9f1"

        # Get and print all devices or a specific device
        this_device = devices_module.get_devices(hwi_device_id)
        if devices:
            print(f"This device {hwi_device_id}:")
            devices_module.auth.print_pretty_json(devices)
        else:
            print("Device not found.")

    if False:
        # Example payload for creating a new device
        payload = {
            "device": {
                "name": "Tenovi Pulse Ox",      # required
                 "hardware_uuid": "c26b2b7d-56dc-412b-be89-d302c52717a5",     # required
            },
        }

        # Create and print the new device
        new_device = devices_module.create_device(payload)
        if new_device:
            print("New Device Created:")
            TenoviAuth.print_pretty_json(new_device)

            """ Returns this
            New Device Created:
            {
                "device": {
                    "created": "2024-05-23T20:51:29.211103Z",
                    "fulfillment_request": null,
                    "hardware_uuid": "C26B2B7D56DC412BBE89D302C52717A5",
                    "id": "f22e0ce6-dd5c-4e38-ba45-aac59d8b985f",
                    "meta_data": null,
                    "name": "Tenovi Pulse Ox",
                    "sensor_code": "11",
                    "shared_hardware_uuid": false
                },
                "id": "83ca5817-0bb2-4d9c-b131-16eb353ad587",
                "patient": null,
                "patient_id": "",
                "patient_phone_number": "",
                "status": "Unknown Gateway ID"
            }
            """

    if False:
            # Get and print all devices or a specific device
            query_params = {
                "properties__key": "pseudo_code_for_tenovi_phi_access",
                "properties__value": "123456789",
            }
            devices = devices_module.get_devices(hwi_device_id=None, **query_params)
            if devices:
                print("Devices by key/value property:")
                devices_module.auth.print_pretty_json(devices)
            else:
                print("Devices: None found.")


    if False:
            # Get and print all devices or a specific device
            devices = devices_module.get_devices(hwi_device_id="83ca5817-0bb2-4d9c-b131-16eb353ad587")
            if devices:
                print("Device by id:")
                devices_module.auth.print_pretty_json(devices)
            else:
                print("Devices: None found.")

    if False:
            # Get and print all devices or a specific device
            devices = devices_module.get_device_by_patient_external_id("AnExternalID")
            if devices:
                print("Devices by patient_external_id :")
                devices_module.auth.print_pretty_json(devices)
            else:
                print("Devices: None found.")


    if False:
            # Get and print all devices or a specific device
            devices = devices_module.get_device_by_patient_external_id("testOmarExternalPatientID")
            if devices:
                print("Devices by patient_external_id :")
                devices_module.auth.print_pretty_json(devices)
            else:
                print("Devices by patient_external_id: None found.")

    if False:
            # Get and print all devices or a specific device
            query_params = {
                "search": "testOmarExternalPatientID",
            }
            devices = devices_module.get_devices(hwi_device_id=None, **query_params)
            if devices:
                print("Devices by search:")
                devices_module.auth.print_pretty_json(devices)
            else:
                print("Devices: None found.")


