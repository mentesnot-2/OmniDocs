const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function postJson<TReq, Tres>(path: string, body: TReq): Promise<Tres> {
    const response = await fetch(`${API_BASE}${path}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    });
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || `Request failed with ${response.status}`);
    }
    return response.json();
}