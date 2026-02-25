"""
Pydantic schemas for the devices feature.

Endpoint → schema mapping:
  GET /api/v1/devices → DevicesResponse
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class DeviceStatus(str, Enum):
    connected    = "connected"
    disconnected = "disconnected"
    unlinked     = "unlinked"


class Device(BaseModel):
    """A single Tenovi device paired with the patient."""
    name: str
    status: DeviceStatus
    hardware_uuid: Optional[str] = None
    created: Optional[str] = None


class DevicesResponse(BaseModel):
    """
    List of devices paired with the patient via Tenovi.

    Mirrors the data used by:
      POST /healthie/iframe_provider_tab/devices
    """
    devices: List[Device]
