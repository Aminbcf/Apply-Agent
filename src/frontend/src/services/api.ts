const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export type ApiErrorShape = {
  detail?: string;
  message?: string;
};

export class ApiError extends Error {
  status: number;
  payload: ApiErrorShape | null;

  constructor(status: number, message: string, payload: ApiErrorShape | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

function getBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getBaseUrl()}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as ApiErrorShape | null;
    throw new ApiError(response.status, payload?.detail ?? payload?.message ?? response.statusText, payload);
  }

  return (await response.json()) as T;
}

export const apiClient = {
  get: <T>(path: string) => requestJson<T>(path),
  post: <T, B extends Record<string, unknown> | undefined = undefined>(path: string, body?: B) =>
    requestJson<T>(path, {
      method: "POST",
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
};

export type HealthResponse = {
  status: string;
};

export type DashboardStats = {
  active_applications: number;
  generated_documents: number;
  interview_sessions: number;
};

export const getDashboardStats = () => apiClient.get<DashboardStats>("/dashboard/stats");

