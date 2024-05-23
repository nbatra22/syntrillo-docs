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




