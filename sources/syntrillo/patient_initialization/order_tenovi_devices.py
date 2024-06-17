

from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.api_tenovi.devices import Devices
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement


class OrderTenoviDevices:
    """
    OrderTenoviDevices class is used to order devices from Tenovi API.

    Args:
        syntrillo_internal_key (str): The internal key of the syntrillo user.

    """


    def __init__(self, syntrillo_internal_key):
        """
        Initialize the OrderTenoviDevices class.
        """
        self.syntrillo_internal_key = syntrillo_internal_key

        # retrieve healthie user id and pseudo code for tenovi phi access
        lookup_codes_management = LookUpCodesManagement()
        entry = lookup_codes_management.retrieve_entry_by_internal_key(syntrillo_internal_key)
        self.healthie_user_id = entry.get('healthie_user_id')
        self.pseudo_code_for_tenovi_phi_access = entry.get('pseudo_code_for_tenovi_phi_access')



    def place_order(
        self,
        devices_names: list = ('Tenovi BPM - L', 'Tenovi BPM - S', 'Tenovi Watch', 'Tenovi Pillbox'),
        gateway_id: str = None,
        sms_opt_in: bool = False,
        healthie_location_index: int = 0,
        pair_devices: bool = True,
        flag_devices: bool = False,
    ):
        """
        This method creates devices with a fulfillment request.

        Args:
            devices_names (list): A list of device names to order. None is allowed, and will be skipped.
            gateway_id (str): Gateway ID. None if not available.
            sms_opt_in (bool): SMS opt-in.
            healthie_location_index (int): The index of the location in the user's locations.
            pair_devices (bool): Pair devices with identifiers and pseudonyms. Default is True.
            flag_devices (bool): Flagged devices are on hold for review. Flag can be removed on the Tenovi portal. Default is False.
        """

        # get user PII
        healthie_utils = HealthieUtils()
        user_pii = healthie_utils.get_user_from_id(self.healthie_user_id)

        # get shippping location
        #  : https://docs.gethealthie.com/schema/location.doc
        location = user_pii['locations'][healthie_location_index]

        # --------------------------------------------------------------------
        # validate the input
        error_flag = False
        error_message = ""
        # make sure the device names are valid
        valid_device_names = ('Tenovi BPM - L', 'Tenovi BPM - S', 'Tenovi Watch', 'Tenovi Pillbox', None)
        for device_name in devices_names:
            if device_name not in valid_device_names:
                error_flag = True
                error_message += f"Invalid device name: {device_name}\n"

        # make sure none of the user_pii fields used below are None
        #  : first_name, last_name, phone_number, email
        for key in ['first_name', 'last_name', 'phone_number', 'email']:
            if user_pii[key] is None:
                error_flag = True
                error_message += f"User PII field {key} is None\n"

        # make sure location fields used below are not None
        #  : line1, line2, city, state, zip
        for key in ['line1', 'line2', 'city', 'state', 'zip']:
            if location[key] is None:
                error_flag = True
                error_message += f"Location field {key} is None\n"

        # --------------------------------------------------------------------
        # create devices
        if error_flag:
            self.created_devices = None
            log = {
                "success": False,
                "error_message": error_message,
            }
        else:
            tenovi_devices = Devices()
            created_devices, created_devices_log = tenovi_devices.create_set_of_devices_with_fulfillment_request(
                # devices
                devices_names = devices_names ,
                gateway_id = gateway_id,

                # pairing
                pair_devices= pair_devices,
                healthie_user_id= self.healthie_user_id,
                pseudo_code_for_tenovi_phi_access= self.pseudo_code_for_tenovi_phi_access,

                # patient
                patient_id = self.healthie_user_id,
                patient_name = user_pii['first_name'] + ' ' + user_pii['last_name'],
                patient_phone_number = user_pii['phone_number'],
                patient_email = user_pii['email'],

                sms_opt_in = sms_opt_in,

                # fulfillment request
                fullfillment_request = True,
                shipping_name = user_pii['first_name'] + ' ' + user_pii['last_name'],
                shipping_address = location['line1'] + '\n' + location['line2'],
                shipping_city = location['city'],
                shipping_state = location['state'],
                shipping_zip_code = location['zip'],
                shipped_on_behalf_of = "",
                shipping_tracking_link = "",
                require_signature = True,
                client_notes = "",
                notify_emails = "",
                client_will_fulfill = False, # must be False for Tenovi to fulfill and dropship
                flagged_by_client = flag_devices,
            )

            self.created_devices = created_devices

            log = {
                "success": created_devices_log['success'],
                "created_devices_log": created_devices_log,
            }

        return log




