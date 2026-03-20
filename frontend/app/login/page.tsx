"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { postJson } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await postJson<{ email: string; password: string }, { user: { id: number; email: string } }>(
        "/auth/login",
        { email, password },
      );
      router.push("/dashboard");
    } catch (err: any) {
      const msg = err?.message || "Login failed"
      if (msg.includes("Email not verified")) {
        setError("Email not verified. Please check your inbox, then login.")
      } else {
        setError(msg)
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950">
      <div className="w-full max-w-md bg-slate-900/80 border border-slate-800 rounded-xl p-8 shadow-xl">
        <div className="flex flex-col items-center mb-6">
          <img src="/OmniDocs.png" alt="OmniDocs" className="h-20 w-auto mb-4" />
          <h1 className="text-2xl font-semibold text-white text-center">
            Log in to OmniDocs
          </h1>
        </div>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm text-slate-300 mb-1">Email</label>
            <input
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              type="email"
              required
              value={email}
              onChange={e => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm text-slate-300 mb-1">Password</label>
            <div className="relative">
              <input
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 pr-10 text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                type={showPassword ? "text" : "password"}
                required
                minLength={1}
                value={password}
                onChange={e => setPassword(e.target.value)}
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute inset-y-0 right-2 my-auto h-7 rounded px-1 text-slate-400 hover:text-slate-200"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
                    <path d="M3 3l18 18" strokeLinecap="round" />
                    <path d="M10.6 10.6a2 2 0 102.8 2.8" strokeLinecap="round" />
                    <path d="M9.88 5.09A10.44 10.44 0 0112 4.9c5.52 0 9.27 5.1 9.9 6-.46.67-2.25 3.1-5 4.7" strokeLinecap="round" />
                    <path d="M6.1 6.1C3.8 7.46 2.36 9.43 2 10c.46.67 4.2 5 10 5 .63 0 1.23-.05 1.8-.14" strokeLinecap="round" />
                  </svg>
                ) : (
                  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
                    <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
          </div>
          {error && (
            <p className="text-sm text-red-400 bg-red-950/40 border border-red-700 rounded-md px-3 py-2">
              {error}
            </p>
          )}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-medium py-2.5 disabled:opacity-60"
          >
            {loading ? "Logging in..." : "Log in"}
          </button>
          <button
            type="button"
            onClick={() => {
              window.location.href = "/api/auth/oauth/google/start";
            }}
            className="w-full rounded-md border border-slate-700 bg-slate-900 text-slate-100 font-medium py-2.5 hover:bg-slate-800"
          >
            Continue with Google
          </button>
          <p className="text-sm text-slate-400 text-center">
            Don&apos;t have an account?{" "}
            <a href="/signup" className="text-emerald-400 hover:underline">
              Sign up
            </a>
          </p>
        </form>
      </div>
    </div>
  );
}