"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { postJson } from "@/lib/api";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await postJson<{ email: string; password: string }, any>(
        "/auth/signup",
        { email, password },
      );
      // Store token & user
      if (typeof window !== "undefined") {
        localStorage.setItem("omnidocs_token", res.access_token);
        localStorage.setItem("omnidocs_user", JSON.stringify(res.user));
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
            <input
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              type="password"
              required
              minLength={8}
              maxLength={128}
              value={password}
              onChange={e => setPassword(e.target.value)}
            />
            <p className="mt-1 text-xs text-slate-500">
              Min 8 chars, uppercase, lowercase, digit, special character
            </p>
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
            {loading ? "Creating account..." : "Sign up"}
          </button>
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