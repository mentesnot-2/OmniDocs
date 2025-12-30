"use client";

import { postJson, getJson } from "@/lib/api";
import { useEffect, useState } from "react";

type UsageRes = {
  plan?: {
    id: string;
    name: string;
    limits: { monthly_queries: number; monthly_uploads: number; storage_mb: number };
  };
  queries_this_month: number;
  uploads_this_month: number;
  storage?: {
    used_bytes: number;
    limit_bytes: number;
    used_percent: number;
  };
};

export default function BillingPage() {
  const [usage, setUsage] = useState<UsageRes | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [portalLoading, setPortalLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    getJson<UsageRes>("/usage/me")
      .then(setUsage)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load usage"))
      .finally(() => setLoading(false));
  }, []);

  async function checkout() {
    setCheckoutLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await postJson<Record<string, never>, { url: string }>("/billing/checkout", {});
      window.location.href = res.url;
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to start checkout");
      setCheckoutLoading(false);
    }
  }

  async function portal() {
    setPortalLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await postJson<Record<string, never>, { url: string }>("/billing/portal", {});
      window.location.href = res.url;
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to open portal");
      setPortalLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <h1 className="text-2xl font-semibold mb-4">Billing & Plan</h1>
      {error && <p className="text-red-400 mb-3">{error}</p>}
      {success && <p className="text-emerald-400 mb-3">{success}</p>}

      {loading ? (
        <p className="text-slate-400">Loading plan details...</p>
      ) : (
        <>
          <p className="mb-2">Current plan: {usage?.plan?.name || "Free"}</p>
          <p>Queries this month: {usage?.queries_this_month ?? 0}</p>
          <p>Uploads this month: {usage?.uploads_this_month ?? 0}</p>
          {usage?.plan?.limits && (
            <div className="mt-4 rounded-lg border border-slate-800 p-4 text-sm text-slate-300 space-y-1">
              <p>Plan limits</p>
              <p>Monthly queries: {usage.plan.limits.monthly_queries}</p>
              <p>Monthly uploads: {usage.plan.limits.monthly_uploads}</p>
              <p>Storage: {usage.plan.limits.storage_mb} MB</p>
            </div>
          )}
          {usage?.storage && (
            <p className="mt-2 text-sm text-slate-400">
              Storage used: {usage.storage.used_percent.toFixed(1)}%
            </p>
          )}
        </>
      )}

      <div className="mt-5 flex gap-3">
        <button
          onClick={checkout}
          disabled={checkoutLoading || loading}
          className="px-4 py-2 rounded bg-emerald-500 text-slate-950 disabled:opacity-50"
        >
          {checkoutLoading ? "Redirecting..." : "Upgrade to Pro"}
        </button>
        <button
          onClick={portal}
          disabled={portalLoading || loading}
          className="px-4 py-2 rounded border border-slate-700 disabled:opacity-50"
        >
          {portalLoading ? "Opening..." : "Manage Subscription"}
        </button>
      </div>
    </div>
  );
}
