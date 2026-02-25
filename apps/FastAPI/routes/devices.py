"""
Devices routes — FastAPI port of the legacy Flask blueprint.

Legacy route → new endpoint mapping:
  POST /healthie/iframe_provider_tab/devices → GET /api/v1/devices

Key differences from the legacy implementation:
  - Returns JSON instead of an HTML template.
  - Device status is inferred from pairing state:
      paired and present  → connected
      absent from list    → no entry returned
  - temporary_lookup_code resolves to syntrillo_internal_key via
    the shared get_syntrillo_internal_key dependency.
"""

import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

SOURCES_PATH = Path(__file__).resolve().parents[3] / "sources"
sys.path.insert(0, str(SOURCES_PATH))

from syntrillo.patient_initialization.accounts_pairing import AccountsPairing
from syntrillo.system.logger import logger

from dependencies import get_syntrillo_internal_key
from schemas.devices import Device, DeviceStatus, DevicesResponse

router = APIRouter()


@router.get("", response_model=DevicesResponse)
def get_devices(
    internal_key: str = Depends(get_syntrillo_internal_key),
):
    """
    Returns the list of Tenovi devices paired with the patient.

    Replaces: POST /healthie/iframe_provider_tab/devices
    """
    try:
        paired_devices = AccountsPairing.get_paired_devices(
            syntrillo_internal_key=internal_key,
        )

        if not paired_devices:
            return DevicesResponse(devices=[])

        devices = []
        for entry in paired_devices:
            device_info = entry.get("device", {})
            name = device_info.get("name") or device_info.get("device_name", "Unknown Device")
            hardware_uuid = device_info.get("hardware_uuid_formatted")
            created = device_info.get("created")

            # A device returned by get_paired_devices is paired with the patient.
            # Treat all paired devices as connected; disconnected/unlinked states
            # will be refined when device sync stats are available.
            devices.append(Device(
                name=name,
                status=DeviceStatus.connected,
                hardware_uuid=hardware_uuid,
                created=created,
            ))

        return DevicesResponse(devices=devices)

    except Exception as e:
        logger.error(f"Error retrieving devices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve devices.",
        )
