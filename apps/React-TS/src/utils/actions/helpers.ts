/**
 * Reusable HTTP helpers for all feature API modules.
 *
 * Covers both auth patterns currently in use:
 *   - Bearer token  (provider sidebar — localStorage)
 *   - Lookup code   (patient tab — query parameter, handled by the caller)
 *
 * Usage:
 *   import { get, post, patch, del, buildQueryString, bearerHeaders, ApiError, isApiError } from './helpers';
 */


// ── Error type ────────────────────────────────────────────────────────────────

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

/** Narrows an unknown catch value to ApiError. */
export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}


// ── Query string ──────────────────────────────────────────────────────────────

type QueryValue = string | number | boolean | null | undefined;

/**
 * Serialize a flat params object into a query string, omitting null/undefined.
 *
 * @example
 * buildQueryString({ temporary_lookup_code: 'abc', start_date: '2025-01-01' })
 * // → "temporary_lookup_code=abc&start_date=2025-01-01"
 */
export function buildQueryString(params: Record<string, QueryValue>): string {
  const usp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      usp.set(key, String(value));
    }
  }
  return usp.toString();
}


// ── Auth ──────────────────────────────────────────────────────────────────────

/**
 * Returns an Authorization header object if a token exists in localStorage,
 * otherwise returns an empty object.
 *
 * Used by provider-facing endpoints that still use the legacy Flask backend.
 */
export function bearerHeaders(): HeadersInit {
  const token = localStorage.getItem('authToken');
  return token ? { Authorization: `Bearer ${token}` } : {};
}


// ── Core request ──────────────────────────────────────────────────────────────

async function request<T>(url: string, init: RequestInit): Promise<T> {
  const response = await fetch(url, init);

  if (!response.ok) {
    throw new ApiError(
      response.status,
      `[${response.status}] ${response.statusText} — ${url}`,
    );
  }

  // 204 No Content — return undefined without trying to parse JSON
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}


// ── CRUD helpers ──────────────────────────────────────────────────────────────

/**
 * GET request returning JSON.
 *
 * @example
 * const data = await get<BPSummaryResponse>(`${BASE}/summary?${qs}`);
 */
export function get<T>(url: string, options?: RequestInit): Promise<T> {
  return request<T>(url, {
    ...options,
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
}

/**
 * POST request with a JSON body.
 *
 * @example
 * const result = await post<CreateResponse>('/api/v1/notes', { text: 'hello' });
 */
export function post<T>(url: string, body: unknown, options?: RequestInit): Promise<T> {
  return request<T>(url, {
    ...options,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    body: JSON.stringify(body),
  });
}

/**
 * POST request with a form-encoded body.
 * Used by legacy Flask endpoints that expect application/x-www-form-urlencoded.
 *
 * @example
 * const result = await postForm<BPData>('/legacy/blood_pressure', { temporary_lookup_code: code });
 */
export function postForm<T>(
  url: string,
  body: Record<string, string>,
  options?: RequestInit,
): Promise<T> {
  return request<T>(url, {
    ...options,
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      ...options?.headers,
    },
    body: new URLSearchParams(body),
  });
}

/**
 * PUT request with a JSON body (full resource replacement).
 *
 * @example
 * const updated = await put<Patient>(`/api/v1/patients/${id}`, patientData);
 */
export function put<T>(url: string, body: unknown, options?: RequestInit): Promise<T> {
  return request<T>(url, {
    ...options,
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    body: JSON.stringify(body),
  });
}

/**
 * PATCH request with a JSON body (partial resource update).
 *
 * @example
 * const updated = await patch<Patient>(`/api/v1/patients/${id}`, { status: 'active' });
 */
export function patch<T>(url: string, body: unknown, options?: RequestInit): Promise<T> {
  return request<T>(url, {
    ...options,
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    body: JSON.stringify(body),
  });
}

/**
 * DELETE request. Use `del<void>` when the endpoint returns 204 No Content.
 *
 * @example
 * await del<void>(`/api/v1/notes/${id}`);
 */
export function del<T>(url: string, options?: RequestInit): Promise<T> {
  return request<T>(url, {
    ...options,
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
}


// ── File download ─────────────────────────────────────────────────────────────

/**
 * Fetch a file and return it as a Blob (e.g. PDF reports).
 *
 * @example
 * const blob = await fetchBlob(`${BASE}/download?${qs}`);
 */
export async function fetchBlob(url: string, options?: RequestInit): Promise<Blob> {
  const response = await fetch(url, { method: 'GET', ...options });
  if (!response.ok) {
    throw new ApiError(
      response.status,
      `[${response.status}] ${response.statusText} — download failed`,
    );
  }
  return response.blob();
}

/**
 * Trigger a browser save-file dialog for a Blob.
 * Call this after fetchBlob resolves.
 *
 * @example
 * const blob = await fetchBlob(url);
 * triggerDownload(blob, 'report.pdf');
 */
export function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}