"use client";

import { useEffect } from "react";

const API_BASE = "/api";
const REFRESH_INTERVAL_MS = 9 * 60 * 1000; // 9 min (access token expires in 15 min)

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    useEffect(() => {
        const refresh = () => {
            fetch(`${API_BASE}/auth/refresh`, { method: "POST", credentials: "include" }).catch(() => {});
        };
        const id = setInterval(refresh, REFRESH_INTERVAL_MS);
        refresh(); // run once on mount
        return () => clearInterval(id);
    }, []);
    return <div>{children}</div>;
}