"use client";

import { postJson, getJson } from "@/lib/api";
import { useEffect, useState } from "react";

type UsageRes = {
  plan?: { id: string; name: string; limits: { monthly_queries: number; monthly_uploads: number; storage_mb: number } };
  queries_this_month: number;
  uploads_this_month: number;
};

export default function BillingPage() {
  const [usage, setUsage] = useState<UsageRes | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getJson<UsageRes>("/usage/me").then(setUsage).catch((e) => setError(e.message));
  }, []);

  async function checkout() {
    try {
      const res = await postJson<Record<string, never>, { url: string }>("/billing/checkout", {});
      window.location.href = res.url;
    } catch (e: any) {
      setError(e.message || "Failed to start checkout");
    }
  }

  async function portal() {
    try {
      const res = await postJson<Record<string, never>, { url: string }>("/billing/portal", {});
      window.location.href = res.url;
    } catch (e: any) {
      setError(e.message || "Failed to open portal");
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <h1 className="text-2xl font-semibold mb-4">Billing & Plan</h1>
      {error && <p className="text-red-400 mb-3">{error}</p>}
      <p className="mb-2">Current plan: {usage?.plan?.name || "Free"}</p>
      <p>Queries this month: {usage?.queries_this_month ?? 0}</p>
      <p>Uploads this month: {usage?.uploads_this_month ?? 0}</p>
      <div className="mt-5 flex gap-3">
        <button onClick={checkout} className="px-4 py-2 rounded bg-emerald-500 text-slate-950">Upgrade to Pro</button>
        <button onClick={portal} className="px-4 py-2 rounded border border-slate-700">Manage Subscription</button>
      </div>
    </div>
  );
}