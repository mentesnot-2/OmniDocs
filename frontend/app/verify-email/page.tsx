"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getJson } from "@/lib/api";

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [message, setMessage] = useState("Verifying your email...");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setError("Missing verification token.");
      setMessage("");
      return;
    }

    getJson<{ detail?: string }>(`/auth/verify/${encodeURIComponent(token)}`)
      .then((res) => {
        setMessage(res.detail || "Email verified successfully.");
        setTimeout(() => router.push("/login"), 1500);
      })
      .catch((err: unknown) => {
        if (err instanceof Error) {
          setError(err.message || "Verification failed.");
        } else {
          setError("Verification failed.");
        }
        setMessage("");
      });
  }, [router, searchParams]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-100 p-6">
      <div className="w-full max-w-md rounded-xl border border-slate-800 bg-slate-900/80 p-6 text-center">
        <h1 className="text-xl font-semibold mb-3">Email Verification</h1>
        {message && <p className="text-emerald-400">{message}</p>}
        {error && <p className="text-red-400">{error}</p>}
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-100 p-6">
          <div className="w-full max-w-md rounded-xl border border-slate-800 bg-slate-900/80 p-6 text-center">
            <p className="text-slate-400">Loading...</p>
          </div>
        </div>
      }
    >
      <VerifyEmailContent />
    </Suspense>
  );
}
