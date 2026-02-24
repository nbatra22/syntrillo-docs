import { buildQueryString, get } from './helpers';
import type { DevicesResponse } from '../types/devices';

// const BASE = '/api/v1/devices';
const BASE = 'http://127.0.0.1:8000/api/v1/devices';

function params(temporaryLookupCode: string): string {
  return buildQueryString({ temporary_lookup_code: temporaryLookupCode });
}


// ── Endpoints ─────────────────────────────────────────────────────────────────

export const devicesApi = {

  /** Devices paired with the patient via Tenovi. */
  getDevices: (temporaryLookupCode: string): Promise<DevicesResponse> =>
    get(`${BASE}?${params(temporaryLookupCode)}`),
};
