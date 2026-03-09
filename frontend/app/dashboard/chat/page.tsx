"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getJson, postJson } from "@/lib/api";

type SessionSummary = { id: number; user_id: number; created_at: string; messages: unknown[] };

export default function ChatPage() {
  const router = useRouter();
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [sources, setSources] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [messageHistory, setMessageHistory] = useState<{question: string, answer: string}[]>([]);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);

  useEffect(() => {
   const params = new URLSearchParams(window.location.search);
   const id = params.get("session");

   if (id) {

    const sid = parseInt(id,10);

    if (isNaN(sid)) return;

    setSessionId(sid);
    getJson<{messages: {role:string,content:string}[]}>(`/chat/sessions/${sid}`)
      .then((res) => {
        const pairs: {question:string,answer:string}[] = [];
        const msgs = res.messages || [];
        for (let i = 0; i < msgs.length - 1; i += 2) {
          if (msgs[i]?.role === "user" && msgs[i + 1]?.role === "assistant") {
            pairs.push({
              question: msgs[i].content,
              answer: msgs[i + 1].content,
            });
          }
        }
        setMessageHistory(pairs);
      })
      .catch((err: any) => {
        setError(err.message || "Failed to fetch chat session");
      });
   } else {
    postJson<Record<string,never>, {id:number}>("/chat/sessions", {})
      .then((res) => {
        setSessionId(res.id);
        window.history.replaceState({},"",`/dashboard/chat?session=${res.id}`);
      })
      .catch((err: any) => {
        setError(err.message || "Failed to create chat session");
      });
   }
  }, []);

  useEffect(() => {
    getJson<SessionSummary[]>("/chat/sessions")
      .then((list) => setSessions(list || []))
      .catch(() => setSessions([]));
  }, [sessionId])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setError(null);
    setAnswer(null);
    setSources([]);
    setLoading(true);
    try {
      const res = await postJson<{ question: string; message_history?: {question:string,answer:string}[]}, { answer: string; sources: string[] }>(
        "/documents/query",
        { question: question.trim(), message_history: messageHistory },
      );
      setAnswer(res.answer);
      setSources(res.sources || []);
      setMessageHistory((prev) => [...prev,{question:question.trim(),answer:res.answer}]);
      if (sessionId) {
        postJson(`/chat/sessions/${sessionId}/messages`, {question:question.trim(),answer:res.answer}).catch(() => {})
      }
      setQuestion("");
    } catch (err: any) {
      setError(err.message || "Query failed");
    } finally {
      setLoading(false);
    }
  }

  function switchSession(id: number) {
    setSessionId(id);
    setMessageHistory([]);
    setAnswer(null);
    setError(null);
    window.location.href = `/dashboard/chat?session=${id}`;
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 px-6 py-4 flex justify-between items-center flex-wrap gap-4">
        <a href="/dashboard" className="flex items-center gap-3">
          <img src="/OmniDocs.png" alt="OmniDocs" className="h-9 w-auto" />
          <span className="text-slate-400 hover:text-white text-sm">← Back to dashboard</span>
        </a>
        {sessions.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-slate-400 text-sm">Sessions:</span>
            <select
              value={sessionId ?? ""}
              onChange={(e) => {
                const v = e.target.value;
                if (v) switchSession(parseInt(v, 10));
              }}
              className="rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">Select session</option>
              {sessions.map((s) => (
                <option key={s.id} value={s.id}>
                  Session {s.id}
                </option>
              ))}
            </select>
          </div>
        )}
      </header>

      <main className="max-w-2xl mx-auto px-6 py-8">
        <h1 className="text-xl font-semibold text-white mb-6">Ask about your documents</h1>
        {messageHistory.length > 0 && (
          <div className="mb-8 space-y-4">
            {messageHistory.map((item, index) => (
              <div key={index} className="rounded-lg border border-slate-700 bg-slate-900/50 p-4 space-y-2">
                <p className="text-sm font-medium text-slate-400">Q: {item.question}</p>
                <p className="text-slate-200 whitespace-pre-wrap">{item.answer}</p>
              </div>
            ))}
          </div>
        )}

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