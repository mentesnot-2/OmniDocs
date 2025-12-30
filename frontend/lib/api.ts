const API_BASE = typeof window !== "undefined" ? "/api" : (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000");

export type DocumentListItem = {
  filename: string;
  uploaded_at: number;
  version: number;
  size_bytes: number;
  status: string;
};

export type DocumentVersionItem = {
  version: number;
  size_bytes: number;
  status: string;
  content_hash: string | null;
  created_at: string | null;
  is_current: boolean;
};

export type IngestionJobStatus = {
  id: number;
  status: string;
  error_message: string | null;
  document_version_id: number;
  created_at: string | null;
  started_at: string | null;
  finished_at: string | null;
};

function extractErrorMessage(data: unknown, status: number): string {
  if (!data || typeof data !== "object") return `Request failed with ${status}`;
  const record = data as Record<string, unknown>;
  if (typeof record.detail === "string") return record.detail;
  if (Array.isArray(record.detail) && record.detail.length > 0) {
    const first = record.detail[0] as { msg?: string };
    if (typeof first?.msg === "string") return first.msg;
  }
  if (typeof record.message === "string") return record.message;
  return `Request failed with ${status}`;
}

async function tryRefresh(): Promise<boolean> {
  if (typeof window === "undefined") return false;
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: getCsrfHeaders(),
      credentials: "include",
    });
    return res.ok;
  } catch {
    return false;
  }
}

async function handleResponse<T>(response: Response, parseJson: () => Promise<T>): Promise<T> {
  if (response.ok) return parseJson();
  const data = await response.json().catch(() => ({}));
  const err = new Error(extractErrorMessage(data, response.status));
  (err as Error & { status?: number }).status = response.status;
  throw err;
}

async function requestWithRefresh(doRequest: () => Promise<Response>): Promise<Response> {
  let response = await doRequest();
  if (response.status === 401 && (await tryRefresh())) {
    response = await doRequest();
  }
  return response;
}

export async function postJson<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  const response = await requestWithRefresh(() =>
    fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getCsrfHeaders(),
      },
      body: JSON.stringify(body),
      credentials: "include",
    })
  );
  return handleResponse(response, () => response.json());
}

export async function patchJson<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  const response = await requestWithRefresh(() =>
    fetch(`${API_BASE}${path}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...getCsrfHeaders(),
      },
      body: JSON.stringify(body),
      credentials: "include",
    })
  );
  return handleResponse(response, () => response.json());
}

export async function postFormData(path: string, formData: FormData): Promise<unknown> {
  const response = await requestWithRefresh(() =>
    fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: getCsrfHeaders(),
      body: formData,
      credentials: "include",
    })
  );
  return handleResponse(response, () => response.json());
}

export async function getJson<T>(path: string): Promise<T> {
  const response = await requestWithRefresh(() =>
    fetch(`${API_BASE}${path}`, {
      method: "GET",
      credentials: "include",
    })
  );
  return handleResponse(response, () => response.json());
}

export async function deleteRequest(path: string): Promise<unknown> {
  const response = await requestWithRefresh(() =>
    fetch(`${API_BASE}${path}`, {
      method: "DELETE",
      headers: getCsrfHeaders(),
      credentials: "include",
    })
  );
  return handleResponse(response, () => response.json());
}

export async function getDocumentVersions(filename: string) {
  return getJson<{ filename: string; versions: DocumentVersionItem[] }>(
    `/documents/${encodeURIComponent(filename)}/versions`
  );
}

export async function getIngestionJob(jobId: number) {
  return getJson<IngestionJobStatus>(`/documents/jobs/${jobId}`);
}

export async function pollIngestionJob(
  jobId: number,
  options?: { intervalMs?: number; timeoutMs?: number }
): Promise<IngestionJobStatus> {
  const intervalMs = options?.intervalMs ?? 1000;
  const timeoutMs = options?.timeoutMs ?? 120000;
  const started = Date.now();

  while (Date.now() - started < timeoutMs) {
    const job = await getIngestionJob(jobId);
    if (job.status === "completed" || job.status === "failed") {
      return job;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  throw new Error("Indexing timed out");
}

function getCookie(name: string): string | null {
  if (typeof window === "undefined") return null;

  const match = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.split("=")[1]) : null;
}

function getCsrfHeaders(): HeadersInit {
  const csrfCookie = getCookie("omnidocs_csrf");
  return csrfCookie ? { "X-CSRF-Token": csrfCookie } : {};
}
