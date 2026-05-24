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

async function requestFormData<T>(path: string, formData: FormData): Promise<T> {
  const response = await fetch(`${getBaseUrl()}${path}`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as ApiErrorShape | null;
    throw new ApiError(response.status, payload?.detail ?? payload?.message ?? response.statusText, payload);
  }

  return (await response.json()) as T;
}

export const apiClient = {
  get: <T>(path: string) => requestJson<T>(path),
  post: <T>(path: string, body?: unknown) =>
    requestJson<T>(path, {
      method: "POST",
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
  patch: <T>(path: string, body?: unknown) =>
    requestJson<T>(path, {
      method: "PATCH",
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
  delete: <T>(path: string) =>
    requestJson<T>(path, {
      method: "DELETE",
    }),
};

export type HealthResponse = {
  status: string;
  models_ready: boolean;
};

export type DashboardStats = {
  active_applications: number;
  generated_documents: number;
  interview_sessions: number;
};

export type OnboardingStatus = {
  status: "pending" | "completed";
  steps_completed: number;
};

export type UserProfileData = {
  full_name: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  career_goals: string | null;
  experience: unknown[];
  education: unknown[];
  projects: unknown[];
  skills: Record<string, unknown>;
  certifications: unknown[];
  languages: unknown[];
  achievements: unknown[];
};

export const getDashboardStats = () => apiClient.get<DashboardStats>("/dashboard/stats");

export const getOnboardingStatus = () => apiClient.get<OnboardingStatus>("/onboarding/status");

export const getProfile = () => apiClient.get<UserProfileData>("/profile/");

export const saveProfile = (profile: UserProfileData) =>
  apiClient.post<UserProfileData>("/profile/", profile);

export const uploadOnboardingCv = (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  return requestFormData<UserProfileData>("/onboarding/upload", formData);
};

export type OnboardingDebugData = {
  raw_cv_text: string | null;
  parsed_cv_json: Record<string, unknown> | null;
  llm_context: Record<string, unknown> | null;
};

export const getOnboardingDebug = () => apiClient.get<OnboardingDebugData>("/onboarding/debug");

// ── Job Application Types ────────────────────────────────────

export type WorkflowStatus = "pending" | "accepted" | "rejected" | "interview" | "ghosted";

export type JobOfferIn = {
  title: string;
  company: string;
  description: string;
  session_id: string;
};

export type DimensionScores = {
  job_match: number;
  skill_match: number;
  education_match: number;
  experience_match: number;
  objective_match: number;
};

export type JobEvaluationOut = {
  job_id: string;
  overall_score: number;
  dimension_scores: DimensionScores;
  workflow_status: WorkflowStatus;
  processing: boolean;
  cv_pdf_url: string | null;
  cover_letter_pdf_url: string | null;
};

export type JobApplicationListOut = {
  job_id: string;
  company_name: string;
  job_title: string;
  match_score: number | null;
  workflow_status: string;
  created_at: string;
  processing: boolean;
  confirmed: boolean;
  cv_text: string | null;
  cover_letter_text: string | null;
};

export type JobStatusOut = {
  job_id: string;
  processing: boolean;
  cv_pdf_url: string | null;
  cover_letter_pdf_url: string | null;
  workflow_status: WorkflowStatus;
};

// ── Job API Calls ────────────────────────────────────────────

export const getJobs = () => apiClient.get<JobApplicationListOut[]>("/jobs");

export const evaluateJob = (data: JobOfferIn) => apiClient.post<JobEvaluationOut>("/jobs/evaluate", data);

export const getJobStatus = (jobId: string) => apiClient.get<JobStatusOut>(`/jobs/${jobId}/status`);

export const deleteJob = (jobId: string) => apiClient.delete<{ job_id: string; deleted: boolean }>(`/jobs/${jobId}`);

export const updateJobStatus = (jobId: string, status: WorkflowStatus) =>
  apiClient.patch<{ job_id: string; workflow_status: string }>(`/jobs/${jobId}/status`, { status });

export const confirmJob = (jobId: string, cvText: string, coverLetterText: string) =>
  apiClient.post<{ job_id: string; confirmed: boolean; cv_pdf_url: string; cover_letter_pdf_url: string }>(
    `/jobs/${jobId}/confirm`,
    { cv_text: cvText, cover_letter_text: coverLetterText }
  );

export const updateJobDocuments = (jobId: string, cvText?: string, coverLetterText?: string) =>
  apiClient.patch<{ job_id: string; saved: boolean }>(`/jobs/${jobId}/documents`, {
    cv_text: cvText,
    cover_letter_text: coverLetterText,
  });

// ── Interview API Calls ──────────────────────────────────────

export const getInterviews = () => apiClient.get<JobApplicationListOut[]>("/interviews");

export const getInterviewDetail = (jobId: string) =>
  apiClient.get<{
    job_id: string;
    company_name: string;
    job_title: string;
    job_description: string;
    match_score: number | null;
    dimension_scores: DimensionScores;
    workflow_status: string;
    confirmed: boolean;
    cv_text: string | null;
    cover_letter_text: string | null;
    cv_pdf_url: string | null;
    cover_letter_pdf_url: string | null;
    created_at: string;
    updated_at: string;
  }>(`/interviews/${jobId}`);

// ── SSE Streaming ────────────────────────────────────────────

export type StreamCallbacks = {
  onCvSectionStart?: (section: string) => void;
  onCvSectionDone?: (section: string, ok: boolean) => void;
  onCvToken: (token: string) => void;
  onCvComplete: (text: string) => void;
  onCoverToken: (token: string) => void;
  onCoverComplete: (text: string) => void;
  onError: (message: string) => void;
  onDone: () => void;
};

function handleStreamEvent(eventType: string, eventData: string, callbacks: StreamCallbacks) {
  try {
    const parsed = JSON.parse(eventData);

    switch (eventType) {
      case "cv_section_start":
        callbacks.onCvSectionStart?.(parsed.section);
        break;
      case "cv_section_done":
        callbacks.onCvSectionDone?.(parsed.section, parsed.ok);
        break;
      case "cv_token":
        callbacks.onCvToken(parsed.token);
        break;
      case "cv_complete":
        callbacks.onCvComplete(parsed.text);
        break;
      case "cover_token":
        callbacks.onCoverToken(parsed.token);
        break;
      case "cover_complete":
        callbacks.onCoverComplete(parsed.text);
        break;
      case "error":
        callbacks.onError(parsed.message);
        break;
      case "done":
        callbacks.onDone();
        break;
    }
  } catch {
    // Skip malformed JSON
  }
}

export async function streamGenerateDocuments(
  jobId: string,
  callbacks: StreamCallbacks,
): Promise<void> {
  const response = await globalThis.fetch(`${getBaseUrl()}/jobs/generate-stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id: jobId }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Stream failed" }));
    callbacks.onError(err.detail ?? "Stream failed");
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    callbacks.onError("No readable stream");
    return;
  }

  await processStreamChunks(reader, callbacks);
}

async function processStreamChunks(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  callbacks: StreamCallbacks
) {
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      processStreamPart(part, callbacks);
    }
  }
}

function processStreamPart(part: string, callbacks: StreamCallbacks) {
  const lines = part.trim().split("\n");
  let eventType = "";
  let eventData = "";

  for (const line of lines) {
    if (line.startsWith("event: ")) {
      eventType = line.slice(7).trim();
    } else if (line.startsWith("data: ")) {
      eventData = line.slice(6);
    }
  }

  if (eventType && eventData) {
    handleStreamEvent(eventType, eventData, callbacks);
  }
}
// ── LLM Settings API ─────────────────────────────────────────────────────────

export type LlmSettingsOut = {
  provider: string;
  external_api_base_url: string;
  external_api_model: string;
  has_api_key: boolean;
  llm_quantize_4bit: boolean;
  llm_max_new_tokens: number;
  llm_use_torch_compile: boolean;
  active_adapter: string;
};

export type LlmSettingsIn = {
  provider: string;
  external_api_base_url?: string;
  external_api_key?: string;
  external_api_model?: string;
  llm_quantize_4bit?: boolean;
  llm_max_new_tokens?: number;
};

export type LlmTestOut = {
  ok: boolean;
  latency_ms: number;
  model_used: string;
  provider: string;
  error?: string;
};

export const getLlmSettings = () =>
  apiClient.get<LlmSettingsOut>("/settings/llm");

export const saveLlmSettings = (payload: LlmSettingsIn) =>
  apiClient.post<LlmSettingsOut>("/settings/llm", payload);

export const testLlmConnection = () =>
  apiClient.get<LlmTestOut>("/settings/llm/test");

// ── Init helpers ───────────────────────────────────────────
/**
 * Fetch and cache the persistent user profile. Call once on app startup
 * so the UI can pre-fill job creation and avoid re-onboarding each time.
 */
let _cachedProfile: UserProfileData | null | undefined = undefined;
export async function initAppProfile(): Promise<UserProfileData | null> {
  if (_cachedProfile !== undefined) return _cachedProfile ?? null;
  try {
    const p = await getProfile();
    _cachedProfile = p;
    return p;
  } catch (err) {
    _cachedProfile = null;
    return null;
  }
}
