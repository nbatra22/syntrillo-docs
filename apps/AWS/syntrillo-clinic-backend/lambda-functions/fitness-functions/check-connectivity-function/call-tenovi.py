import json

from syntrillo.api_tenovi.devices import Devices

devices = Devices().get_devices_by_pseudo_code(
    pseudo_code_for_tenovi_phi_access__uuid = 'c4bcf6f1-c060-4e44-a931-47d71c251da3'
)[0]

print(json.dumps(devices))