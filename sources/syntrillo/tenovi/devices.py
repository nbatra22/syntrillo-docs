from auth import TenoviAuth

class Devices:
    def __init__(self, client_domain="syntrillo"):
        self.client_domain = client_domain
        self.auth = TenoviAuth()

    def get_devices(self, hwi_device_id=None, **kwargs):
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

    def create_device(self, payload):
        """
        Creates a new HWI Device with optional Fulfillment Request

        A nested Device object is required. Within this object, the Device name must exactly match the name of a Device Type associated with your account. You may use the hwi-device-types endpoint to view a complete list of Device Types associated with your account.

        You can also optionally link this Device to a Patient by including a nested Patient object. If you do this, the "external_id" field can be used to uniquely identify this Patient. For example, if you edit the name or phone_number of a Patient, those fields will be updated for all Devices the same Patient external_id. We thus recommend Clients use a unique Patient identifier from their own systems for this field (hence the name "external_id").

        https://api2.tenovi.com/hwi-redoc/#tag/hwi-devices
        """
        url = f"https://api2.tenovi.com/clients/{self.client_domain}/hwi/hwi-devices/"
        return self.auth.make_post_request(url, payload)

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




