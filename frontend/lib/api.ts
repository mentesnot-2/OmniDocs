const API_BASE = typeof window !== "undefined" ? "/api" : (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");

export async function postJson<TReq, Tres>(path: string, body: TReq): Promise<Tres> {
    const response = await fetch(`${API_BASE}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        credentials: "include",
    });
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || `Request failed with ${response.status}`);
    }
    return response.json();
}

export async function postFormData(path: string, formData: FormData): Promise<any> {
    const response = await fetch(`${API_BASE}${path}`, {
        method: "POST",
        body: formData,
        credentials: "include",
    });

    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || `Request failed with ${response.status}`);
    }
    return response.json();
}

export async function getJson<T>(path: string): Promise<T> {
    const response = await fetch(`${API_BASE}${path}`, {
        method: "GET",
        credentials: "include",
    });
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || `Request failed with ${response.status}`);
    }
    return response.json();
}


export async function deleteRequest(path: string): Promise<any> {
    const response = await fetch(`${API_BASE}${path}`, {
        method: "DELETE",
        credentials: "include",
    });

    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || `Request failed with ${response.status}`);
    }
    return response.json();
}