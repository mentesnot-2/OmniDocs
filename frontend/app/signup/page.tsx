"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { postJson } from "@/lib/api";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  const constraints = [
    { label: "At least 8 characters", valid: password.length >= 8 },
    { label: "At most 128 characters", valid: password.length <= 128 },
    { label: "At least one uppercase letter", valid: /[A-Z]/.test(password) },
    { label: "At least one lowercase letter", valid: /[a-z]/.test(password) },
    { label: "At least one digit", valid: /\d/.test(password) },
    { label: "At least one special character", valid: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?]/.test(password) },
  ];
  const isPasswordValid = constraints.every((c) => c.valid);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await postJson<{ email: string; password: string }, { detail?: string }>(
        "/auth/signup",
        { email, password },
      );

      if (res?.detail?.includes("Verification email sent")) {
        setInfo("Verification email sent. Please check your inbox, then log in.");
        setTimeout(() => router.push("/login"), 1500);
        return;
      }
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Signup failed");
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
            Create your OmniDocs account
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
                minLength={8}
                maxLength={128}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
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
            <ul className="mt-2 space-y-1 text-xs">
              {constraints.map((c) => (
                <li key={c.label} className={c.valid ? "text-emerald-400" : "text-red-400"}>
                  {c.valid ? "✓" : "•"} {c.label}
                </li>
              ))}
            </ul>
          </div>
          {error && (
            <p className="text-sm text-red-400 bg-red-950/40 border border-red-700 rounded-md px-3 py-2">
              {error}
            </p>
          )}
          <button
            type="submit"
            disabled={loading || !isPasswordValid}
            className="w-full rounded-md bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-medium py-2.5 disabled:opacity-60"
          >
            {loading ? "Creating account..." : "Sign up"}
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
          {info && (
            <p className="text-sm text-emerald-400 bg-emerald-950/30 border border-emerald-700 rounded-md px-3 py-2">
              {info}
            </p>
          )}
          <p className="text-sm text-slate-400 text-center">
            Already have an account?{" "}
            <a href="/login" className="text-emerald-400 hover:underline">
              Log in
            </a>
          </p>
        </form>
      </div>
    </div>
  );
}