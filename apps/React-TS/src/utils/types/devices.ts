/**
 * TypeScript types for the devices API response.
 * Mirrors the FastAPI Pydantic schemas in apps/FastAPI/schemas/devices.py.
 */

// ── GET /api/v1/devices ───────────────────────────────────────────────────────

export type DeviceStatus = 'connected' | 'disconnected' | 'unlinked';

export interface Device {
  name: string;
  status: DeviceStatus;
  hardware_uuid?: string | null;
  created?: string | null;
}

export interface DevicesResponse {
  devices: Device[];
}
