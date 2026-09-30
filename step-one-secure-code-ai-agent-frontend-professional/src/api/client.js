export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

export class ApiError extends Error {
  constructor(message, { code = 'API_ERROR', status = 0, requestId = null } = {}) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.requestId = requestId;
  }
}

export async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: 'no-store',
    credentials: 'same-origin',
    ...options,
    headers: {
      Accept: 'application/json',
      ...options.headers,
    },
  });
  const contentType = response.headers.get('content-type') ?? '';
  const payload = contentType.includes('application/json')
    ? await response.json()
    : null;

  if (!response.ok) {
    const error = payload?.error;
    throw new ApiError(
      error?.message ?? `Request failed with status ${response.status}.`,
      {
        code: error?.code,
        status: response.status,
        requestId: error?.request_id ?? response.headers.get('x-request-id'),
      },
    );
  }

  return payload;
}
