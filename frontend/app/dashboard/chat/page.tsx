"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { postJson } from "@/lib/api";

export default function ChatPage() {
  const router = useRouter();
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [sources, setSources] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setError(null);
    setAnswer(null);
    setSources([]);
    setLoading(true);
    try {
      const res = await postJson<{ question: string }, { answer: string; sources: string[] }>(
        "/documents/query",
        { question: question.trim() },
      );
      setAnswer(res.answer);
      setSources(res.sources || []);
    } catch (err: any) {
      setError(err.message || "Query failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 px-6 py-4 flex justify-between items-center">
        <a href="/dashboard" className="text-slate-400 hover:text-white text-sm">
          ← Back to dashboard
        </a>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-8">
        <h1 className="text-xl font-semibold text-white mb-6">Ask about your documents</h1>

        <form onSubmit={handleSubmit} className="space-y-4 mb-8">
          <input
            type="text"
            placeholder="e.g. What is OmniDocs?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading}
            className="w-full rounded-md border border-slate-700 bg-slate-900 px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={loading}
            className="rounded-md bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-medium px-4 py-2"
          >
            {loading ? "Thinking..." : "Ask"}
          </button>
        </form>

        {error && (
          <div className="rounded-md border border-red-800 bg-red-950/40 px-4 py-3 text-red-400 mb-6">
            {error}
          </div>
        )}

        {answer && (
          <div className="space-y-4 mb-6">
            <div className="rounded-md border border-slate-700 bg-slate-900/50 px-4 py-4 text-slate-200 whitespace-pre-wrap">
              {answer}
            </div>
            {sources.length > 0 && (
              <div className="text-sm text-slate-400">
                <span className="font-medium text-slate-300">Sources: </span>
                {sources.join(", ")}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}