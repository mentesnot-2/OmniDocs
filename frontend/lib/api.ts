const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken() : string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("omnidocs_token") || null;
}


export async function postJson<TReq, Tres>(path: string, body: TReq): Promise<Tres> {
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
    };
    const token = getToken();
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    const response = await fetch(`${API_BASE}${path}`, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
    });
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || `Request failed with ${response.status}`);
    }
    return response.json();
}

export async function postFormData(path:string, formData:FormData) : Promise<any> {
    const token = getToken();
    const headers: Record<string, string> = {}

    if (token) headers["Authorization"] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE}${path}`, {
        method: "POST",
        headers,
        body: formData,
    });

    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || `Request failed with ${response.status}`);
    }
    return response.json();
}

export async function getJson<T>(path:string) : Promise<T> {
    const token = getToken();
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;


    const response = await fetch(`${API_BASE}${path}`, {
        method: "GET",
        headers,
    });
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || `Request failed with ${response.status}`);
    }
    return response.json();
}