const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

let accessToken: string | null = null;
let refreshToken: string | null = null;

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return accessToken;
  return localStorage.getItem("access_token");
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return refreshToken;
  return localStorage.getItem("refresh_token");
}

export function setTokens(access: string, refresh: string) {
  accessToken = access;
  refreshToken = refresh;
  if (typeof window !== "undefined") {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
  }
}

export function clearTokens() {
  accessToken = null;
  refreshToken = null;
  if (typeof window !== "undefined") {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // use default
    }
    throw new ApiError(detail, response.status);
  }
  return response.json() as Promise<T>;
}

async function fetchWithAuth(
  path: string,
  init: RequestInit,
  params?: Record<string, string | number | undefined>
): Promise<Response> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
  };

  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    });
  }

  let response = await fetch(url.toString(), { ...init, headers });

  // Auto-refresh on 401
  if (response.status === 401) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      const newToken = getAccessToken();
      if (newToken) {
        headers.Authorization = `Bearer ${newToken}`;
        response = await fetch(url.toString(), { ...init, headers });
      }
    } else {
      clearTokens();
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }
  }

  return response;
}

async function refreshAccessToken(): Promise<boolean> {
  const refresh = getRefreshToken();
  if (!refresh) return false;

  try {
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });

    if (response.ok) {
      const data = await response.json();
      setTokens(data.access_token, data.refresh_token);
      return true;
    }
  } catch {
    // ignore
  }
  return false;
}

export async function apiGet<T>(
  path: string,
  params?: Record<string, string | number | number | undefined>
): Promise<T> {
  const response = await fetchWithAuth(path, { method: "GET" }, params);
  return handleResponse<T>(response);
}

export async function apiPost<T, B = unknown>(
  path: string,
  body?: B
): Promise<T> {
  const response = await fetchWithAuth(path, {
    method: "POST",
    body: body ? JSON.stringify(body) : undefined,
  });
  return handleResponse<T>(response);
}

export async function apiPatch<T, B = unknown>(
  path: string,
  body?: B
): Promise<T> {
  const response = await fetchWithAuth(path, {
    method: "PATCH",
    body: body ? JSON.stringify(body) : undefined,
  });
  return handleResponse<T>(response);
}

export async function apiPut<T, B = unknown>(
  path: string,
  body?: B
): Promise<T> {
  const response = await fetchWithAuth(path, {
    method: "PUT",
    body: body ? JSON.stringify(body) : undefined,
  });
  return handleResponse<T>(response);
}

export async function apiDelete(path: string): Promise<void> {
  const response = await fetchWithAuth(path, { method: "DELETE" });
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // use default
    }
    throw new ApiError(detail, response.status);
  }
}

// Zod-validated versions
export async function apiGetValidated<T>(
  path: string,
  schema: { parse: (data: unknown) => T },
  params?: Record<string, string | number | undefined>
): Promise<T> {
  const response = await fetchWithAuth(path, { method: "GET" }, params);
  const data = await response.json();
  return schema.parse(data);
}

export async function apiPostValidated<T, B = unknown>(
  path: string,
  schema: { parse: (data: unknown) => T },
  body?: B
): Promise<T> {
  const response = await fetchWithAuth(path, {
    method: "POST",
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json();
  return schema.parse(data);
}

export async function apiPatchValidated<T, B = unknown>(
  path: string,
  schema: { parse: (data: unknown) => T },
  body?: B
): Promise<T> {
  const response = await fetchWithAuth(path, {
    method: "PATCH",
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json();
  return schema.parse(data);
}

export { TokenResponseSchema } from "@/lib/validators/auth";