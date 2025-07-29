# Path: ./sources/syntrillo/api_tenovi/devices.py

import json
import uuid
from typing import Tuple

from syntrillo.api_tenovi.auth import TenoviAuth
from syntrillo.api_tenovi.device_properties import DeviceProperties


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
    def __init__(self):
        self.auth = TenoviAuth()

    def device_dict_format_hardware_uuid(self, device: dict) -> dict:
        """
        Adds a field 'hardware_uuid_formatted' to the device dictionary,
        formatting the 'hardware_uuid' with hyphens every 4 characters.

        Args:
            device (dict): A dictionary that may contain a 'hardware_uuid' field.

        Returns:
            dict: The updated device dictionary with the new 'hardware_uuid_formatted' field added.
        """
        if device is not None and 'device' in device and 'hardware_uuid' in device['device']:
            uuid = device['device']['hardware_uuid']
            if uuid is None:
                formatted_uuid = None
            else:
                formatted_uuid = '-'.join(uuid[i:i+4] for i in range(0, len(uuid), 4))
            device['device']['hardware_uuid_formatted'] = formatted_uuid

        return device

    def devices_format_hardware_uuid(self, devices: list) -> list:
        """
        Adds a field 'hardware_uuid_formatted' to each device in the devices list,
        formatting the 'hardware_uuid' with hyphens every 4 characters.

        Args:
            devices (list): List of devices, where each device is a dictionary that may contain a 'hardware_uuid' field.

        Returns:
            list: The updated list of devices with the new 'hardware_uuid_formatted' field added.
        """
        if type(devices) is dict:
            devices = self.device_dict_format_hardware_uuid(devices)

        elif type(devices) is list:
            for device in devices:
                device = self.device_dict_format_hardware_uuid(device)
        else:
            raise ValueError(f"devices must be a list or dict, not {type(devices)}")

        return devices


    def get_devices(self, hwi_device_id: str = None, **kwargs) -> Tuple[list, dict]:
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

        Args:
            hwi_device_id (str): The HWI Device ID.
            **kwargs: Query parameters.

        Returns a tupple:
            list: A list of device dictionaries.
            dict: The log of the request.

        """

        url = "/hwi/hwi-devices/"
        if hwi_device_id:
            url += f"{hwi_device_id}/"

        devices, log = self.auth.make_get_request(url, params=kwargs)

        if devices is None:
            return None, log

        return self.devices_format_hardware_uuid(devices), log


    def get_devices_by_patient_external_id(self, external_id: str) -> Tuple[list, dict]:
        """
        Returns devices matching patient external ID

        Args:
            external_id (str): The external ID of the patient.

        Returns a tupple:
            list: A list of device dictionaries.
            dict: The log of the request.
        """
        query_params = {
            "patient__external_id": external_id,
        }
        return self.get_devices(**query_params)

    def get_devices_by_pseudo_code(self, pseudo_code_for_tenovi_phi_access__uuid: uuid.UUID) -> Tuple[list, dict]:
        """
        Returns devices matching the pseudo_code_for_tenovi_phi_access key/value property

        The pseudo_code_for_tenovi_phi_access represents the pseudo code for Tenovi PHI access.

        The pseudo_code_for_tenovi_phi_access is stored/searched for as a str(uuid.UUID)

        Args:
            pseudo_code_for_tenovi_phi_access__uuid (uuid.UUID): The pseudo code for Tenovi PHI access.

        Returns a tupple:
            list: A list of device dictionaries.
            dict: The log of the request.
        """
        query_params = {
            "properties__key": "pseudo_code_for_tenovi_phi_access",
            "properties__value": str(pseudo_code_for_tenovi_phi_access__uuid), # str(uuid.UUID) : important to convert to string
        }
        return self.get_devices(**query_params)


    def create_device(self, payload: dict) -> Tuple[dict, dict]:
        """
        Creates a new HWI Device with optional Fulfillment Request

        A nested Device object is required. Within this object, the Device name must exactly match the name of a Device Type associated with your account. You may use the hwi-device-types endpoint to view a complete list of Device Types associated with your account.

        You can also optionally link this Device to a Patient by including a nested Patient object. If you do this, the "external_id" field can be used to uniquely identify this Patient. For example, if you edit the name or phone_number of a Patient, those fields will be updated for all Devices the same Patient external_id. We thus recommend Clients use a unique Patient identifier from their own systems for this field (hence the name "external_id").

        https://api2.tenovi.com/hwi-redoc/#tag/hwi-devices

        Args:
            payload (dict): The device data.

        Returns a tupple:
            dict: The created device dictionary.
            dict: The log of the request.
        """
        url = "/hwi/hwi-devices/"

        return self.auth.make_post_request(url, payload)


    def update_device_patient_id(self, hwi_device_id: str, patient_id: str) -> Tuple[dict, dict]:
        """
        Updates the patient_id of a device.

        See https://api2.tenovi.com/hwi-redoc/#operation/hwi-devices_partial_update

        Args:
            hwi_device_id (str): The HWI Device ID.
            patient_id (str): The patient ID.

        Returns a tupple:
            dict: The updated device dictionary.
            dict: The log of the request.
        """

        # get additional device data
        this_device, _ = self.get_devices(hwi_device_id)

        url = f"/hwi/hwi-devices/{hwi_device_id}/"
        payload = {
            "patient_id": patient_id,
            "device" : {
                "name": this_device['device']['name'],
                "hardware_uuid": this_device['device']['hardware_uuid'],
            },
            "patient" : {
                "external_id": patient_id,
                "name": this_device['patient']['name'], # to left it unchanged
            },
        }
        return self.auth.make_patch_request(url, payload)

    def create_set_of_devices_with_fulfillment_request(
        self,
        # devices
        devices_names: list = ('Tenovi BPM - L', 'Tenovi BPM - S', 'Tenovi Watch', 'Tenovi Pillbox', 'Omron BPM'),

        # pairing
        pair_devices: bool = True,
        healthie_user_id: str = None,
        pseudo_code_for_tenovi_phi_access__uuid: uuid.UUID = None,  # : uuid.UUID

        # patient
        patient_id: str = "TempCode",
        patient_name: str = None,
        patient_phone_number: str = "",
        patient_email: str = None,

        # gateway
        gateway_id: str = None,

        # fulfillment request
        fullfillment_request: bool = True,

        shipping_name: str = None,
        shipping_address: str = None,
        shipping_city: str = None,
        shipping_state: str = None,
        shipping_zip_code: str = None,
        shipped_on_behalf_of: str = None,
        shipping_tracking_link: str = None,
        require_signature: bool = True,
        client_notes: str = None,
        notify_emails: str = None,
        client_will_fulfill: bool = False, # False will request a dropship by Tenovi ('Dropship Requested' status in the dashboard)
        flagged_by_client: bool = None,

        sms_opt_in: bool = False, # If you have not obtained the patient's consent to receive SMS messages, please set the sms_opt_in field to False.
    ):
        """
        Creates a new set of HWI Devices with optional Fulfillment Request for each device.

        Args:
            devices_names (list): List of device names to be created. Default includes 'Tenovi BPM - L', 'Tenovi BPM - S', 'Tenovi Watch', 'Tenovi Pillbox'. None

            pair_devices (bool): Whether to pair the devices. Default is True.
            healthie_user_id (str): The Healthie User ID to pair the devices with.
            pseudo_code_for_tenovi_phi_access__uuid (uuid.UUID): The pseudo code for Tenovi PHI access.

            allowed and will be ignored.
            patient_id (str): The ID of the patient.
            patient_name (str): The name of the patient.
            patient_external_id (str): The external ID of the patient. Will be displayed on the Device Dashboard as 'Patient ID'
            patient_phone_number (str): The phone number of the patient.
            patient_email (str): The email of the patient.

            gateway_id (str): The gateway ID (if applicable). If None, a new gateway ID will be shipped as well.

            fulfillment_request (bool): Whether to include a fulfillment request. Default is True.

            shipping_name (str): The name for shipping.
            shipping_address (str): The address for shipping.
            shipping_city (str): The city for shipping.
            shipping_state (str): The state for shipping.
            shipping_zip_code (str): The zip code for shipping.
            shipped_on_behalf_of (str): The entity on behalf of which the shipment is made.
            shipping_tracking_link (str): The tracking link for the shipment.
            require_signature (bool): Whether a signature is required upon delivery. Default is True.
            client_notes (str): Additional notes from the client.
            notify_emails (str): Emails to notify.
            client_will_fulfill (bool): Whether the client will fulfill the request internally. Default is False (Tenovi will dropship the devices).
            flagged_by_client (bool): Whether the request is flagged by the client.

            sms_opt_in (bool): Whether the patient has opted in for SMS notifications. Default is False.

        Returns a tupple
            list: List of created devices.
            log: The log of the request.

        Raises:
            ValueError: If patient ID or device name is missing.
        """

        devices_created = []
        overall_log = {
            "success": True,
            "log": [],
        }
        for device_name in devices_names:
            if device_name is not None:

                # Check this device does not exist already
                #  : same patient_id, same device_name, same gateway_id
                current_patient_devices, _ = self.get_devices_by_patient_external_id(patient_id)
                duplicated_device = False
                for device in current_patient_devices:
                    if device['device']['name'] == device_name  and device['device']['hardware_uuid'] == gateway_id:
                        duplicated_device = True
                        break

                if duplicated_device:
                    overall_log["log"].append({
                        "new_device": {
                            "device_name": device_name,
                            "error_message": "Device and gateway already exists for this patient",
                        },
                        "pairing": None,
                    })
                    overall_log["success"] = False
                else:
                    # all fine, let's create the device and pair it
                    payload = {
                        "patient_id": patient_id,
                        "patient_phone_number": patient_phone_number,
                        "patient" : {
                            "external_id": patient_id, # Will be displayed on the Device Dashboard as 'Patient ID'
                            "name": patient_name,
                            "phone_number": patient_phone_number,
                            "email": patient_email,
                            "physician": None, # If the physician field is included in the Patient object, this data will be forwarded to our fulfillment team (if dropshipping is requested) to allow for any per-provider shipping customizations (additional charges may apply).
                            "clinic_name": "Syntrillo Clinic",
                            "care_manager": None,
                            "sms_opt_in": sms_opt_in ,
                        },
                        "device": {
                            "name": device_name,
                            "hardware_uuid": gateway_id,  # that's the Gateway ID
                        },
                    }

                    if fullfillment_request:
                        payload["device"]["fulfillment_request"] = {
                            "shipping_name": shipping_name,
                            "shipping_address": shipping_address,
                            "shipping_city": shipping_city,
                            "shipping_state": shipping_state,
                            "shipping_zip_code": shipping_zip_code,
                            "shipped_on_behalf_of": shipped_on_behalf_of,
                            "shipping_tracking_link": shipping_tracking_link,
                            "require_signature": require_signature,
                            "client_notes": client_notes,
                            "notify_emails": notify_emails,
                            "client_will_fulfill": client_will_fulfill,
                            "flagged_by_client": flagged_by_client
                        }

                    # add device
                    new_device, log_new_device = self.create_device(payload)
                    devices_created.append(new_device)

                    # pair device
                    #  : pairing done with creation to prevent orphaned devices is something goes wrong with creation of next devices
                    if pair_devices:

                        if new_device is None:
                            log_pairing = {
                                "success": False,
                                "error_message": "Device is None",
                            }

                        elif new_device['id'] is None:
                            log_pairing = {
                                "success": False,
                                "error_message": "Device ID is None",
                            }

                        else:

                            device_properties = DeviceProperties()

                            _, log1 = device_properties.create__healthie_user_id__property(
                                hwi_device_id = new_device['id'],
                                healthie_user_id = healthie_user_id,
                            )

                            _, log2 = device_properties.create__pseudo_code_for_tenovi_phi_access__property(
                                hwi_device_id = new_device['id'],
                                pseudo_code_for_tenovi_phi_access = pseudo_code_for_tenovi_phi_access__uuid,
                            )

                            log_pairing = {
                                "success": log1['success'] and log2['success'],
                                "log1": log1,
                                "log2": log2
                            }

                    overall_log["log"].append({
                        "new_device": log_new_device,
                        "pairing": log_pairing,
                    })
                    overall_log["success"] = overall_log["success"] and log_new_device["success"] and log_pairing["success"]

        return devices_created, overall_log

    def delete_device(self, hwi_device_id: str) -> Tuple[dict, dict]:
        """
        Deletes a HWI Device.

        Args:
            hwi_device_id (str): The HWI Device ID.

        Returns a tupple:
            dict: The response of the request.
            dict: The success log.
        """
        url = f"/hwi/hwi-devices/{hwi_device_id}/"
        return self.auth.make_delete_request(url)


# Example usage:
if __name__ == "__main__":
    devices_module = Devices()

    if False:
        # Get and print all devices or a specific device
        devices, log = devices_module.get_devices()
        if devices:
            print("Devices:")
            devices_module.auth.print_pretty_json(devices)
            print("--------------")
            for device in devices:
                print(f"Device ID: {device['id']}, Patient ID: {device['patient_id']}")

        else:
            print("Devices: None found.")
            print(log)

    # List Omar new devices
    if True:
        device_ids = [
                   "e154d35e-4543-4c15-abdd-cbdc8f482654",  # Omar New - HWI - Watch
                   "55fc9fab-3a74-4d61-b949-c1f08ea76f2b",  # Omar New - HWI - Pillbox
                   "ff7ddf32-1472-450e-89ae-362416765d8b",  # Omar New - HWI - BPM
                   # "425ed808-4144-4c86-aa7f-921c5b16a5f8",  # test 1
                   # "8b9d1441-eadd-42c6-a491-34192526bb04", # test 2
                   ]

        # Get and print all devices or a specific device
        for hwi_device_id in device_ids:
            this_device, log = devices_module.get_devices(hwi_device_id)
            if this_device:
                print(f"This device {hwi_device_id}:")
                devices_module.auth.print_pretty_json(this_device)
            else:
                print("Device not found.", hwi_device_id)
                print(log)

    # test create_set_of_devices_with_fulfillment_request
    if False:
        created_devices, log = devices_module.create_set_of_devices_with_fulfillment_request(
            devices_names = ('Tenovi BPM - L', 'Tenovi Watch', 'Tenovi Pillbox'),
            patient_id = "123456789",
            patient_name = "Test Patient",
            gateway_id = "1234-5678-0000",
            fullfillment_request=False,
        )

        devices_module.auth.print_pretty_json(created_devices)

        devices_module.auth.print_pretty_json(log)
