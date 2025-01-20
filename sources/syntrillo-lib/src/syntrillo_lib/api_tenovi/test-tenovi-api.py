# Path: ./sources/syntrillo/api_tenovi/test-tenovi-api.py
import sys
sys.path.append('/home/olivier/SyntrilloClinic/sources')

from devices import Devices

devices = Devices()
print(devices.get_devices_by_pseudo_code('564c8031-da06-4f7e-9057-44c4b790547d'))