const API_BASE = typeof window !== "undefined" ? "/api" : (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");

/** Call /auth/refresh to get new tokens. Returns true if refresh succeeded. */
async function tryRefresh(): Promise<boolean> {
    if (typeof window === "undefined") return false;
    try {
        const res = await fetch(`${API_BASE}/auth/refresh`, {
            method: "POST",
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
    const err = new Error(data.detail || `Request failed with ${response.status}`);
    (err as Error & { status?: number }).status = response.status;
    throw err;
}

export async function postJson<TReq, Tres>(path: string, body: TReq): Promise<Tres> {
    const doRequest = () =>
        fetch(`${API_BASE}${path}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
            credentials: "include",
        });
    let response = await doRequest();
    if (response.status === 401 && (await tryRefresh())) {
        response = await doRequest();
    }
    return handleResponse(response, () => response.json());
}

export async function postFormData(path: string, formData: FormData): Promise<any> {
    const doRequest = () =>
        fetch(`${API_BASE}${path}`, {
            method: "POST",
            body: formData,
            credentials: "include",
        });
    let response = await doRequest();
    if (response.status === 401 && (await tryRefresh())) {
        response = await doRequest();
    }
    return handleResponse(response, () => response.json());
}

export async function getJson<T>(path: string): Promise<T> {
    const doRequest = () =>
        fetch(`${API_BASE}${path}`, {
            method: "GET",
            credentials: "include",
        });
    let response = await doRequest();
    if (response.status === 401 && (await tryRefresh())) {
        response = await doRequest();
    }
    return handleResponse(response, () => response.json());
}

export async function deleteRequest(path: string): Promise<any> {
    const doRequest = () =>
        fetch(`${API_BASE}${path}`, {
            method: "DELETE",
            credentials: "include",
        });
    let response = await doRequest();
    if (response.status === 401 && (await tryRefresh())) {
        response = await doRequest();
    }
    return handleResponse(response, () => response.json());
}