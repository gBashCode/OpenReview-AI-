/**
 * Centralized Typed API Client for OpenReview AI backend.
 * Provides JWT token attachment, standard error handling, and Server-Sent Events (SSE).
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export class ApiError extends Error {
  code: string;
  status: number;
  details?: any;

  constructor(message: string, status: number, code: string = 'API_ERROR', details?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export function getAuthToken(): string | null {
  return localStorage.getItem('openreview_token');
}

export function setAuthToken(token: string | null): void {
  if (token) {
    localStorage.setItem('openreview_token', token);
  } else {
    localStorage.removeItem('openreview_token');
  }
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const defaultHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };

  const token = getAuthToken();
  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...(options.headers as Record<string, string>),
    },
  });

  if (response.status === 204) {
    return {} as T;
  }

  if (response.status === 401) {
    setAuthToken(null);
    if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/landing')) {
      window.location.href = '/login';
    }
  }

  const contentType = response.headers.get('content-type');
  const isJson = contentType && contentType.includes('application/json');
  const data = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const errorPayload = data && typeof data === 'object' && 'error' in data ? (data as any).error : null;
    throw new ApiError(
      errorPayload?.message || (typeof data === 'object' && 'message' in data ? (data as any).message : null) || response.statusText || 'Request failed',
      response.status,
      errorPayload?.code || 'HTTP_ERROR',
      errorPayload?.details || data
    );
  }

  return data as T;
}

/**
 * Server-Sent Events (SSE) subscriber for real-time review updates.
 */
export function subscribeToEventStream(
  endpoint: string,
  onEvent: (event: string, data: any) => void,
  onError?: (err: any) => void
): () => void {
  const url = `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  const eventSource = new EventSource(url);

  eventSource.addEventListener('status_update', (e: MessageEvent) => {
    try {
      const parsed = JSON.parse(e.data);
      onEvent('status_update', parsed);
    } catch {
      onEvent('status_update', e.data);
    }
  });

  eventSource.addEventListener('completed', (e: MessageEvent) => {
    try {
      const parsed = JSON.parse(e.data);
      onEvent('completed', parsed);
    } catch {
      onEvent('completed', e.data);
    }
    eventSource.close();
  });

  eventSource.addEventListener('error', (e: any) => {
    if (onError) onError(e);
  });

  return () => {
    eventSource.close();
  };
}
