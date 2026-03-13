"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getJson, postJson } from "@/lib/api";

type Msg = { role: string; content: string };
type SessionSummary = { id: number; user_id: number; created_at: string; messages: Msg[] };

function getSessionTitle(session: SessionSummary, maxLen = 36): string {
  const firstUser = session.messages?.find((m) => m.role === "user");
  const text = firstUser?.content?.trim();
  if (!text) return "New chat";
  return text.length <= maxLen ? text : text.slice(0, maxLen) + "…";
}

export default function ChatPage() {
  const router = useRouter();
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messageHistory, setMessageHistory] = useState<{question: string, answer: string, sources?: string[]}[]>([]);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);

  function loadSessionMessages(sid: number) {
    getJson<{messages: Msg[]}>(`/chat/sessions/${sid}`)
      .then((res) => {
        const pairs: {question: string, answer: string, sources?: string[]}[] = [];
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
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to fetch chat session");
      });
  }

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const id = params.get("session");

    if (id) {
      const sid = parseInt(id, 10);
      if (!isNaN(sid)) {
        setSessionId(sid);
        loadSessionMessages(sid);
      }
      getJson<SessionSummary[]>("/chat/sessions")
        .then((list) => setSessions(list || []))
        .catch(() => setSessions([]));
      return;
    }

    // No session in URL: reuse an empty session if one exists, otherwise create new
    getJson<SessionSummary[]>("/chat/sessions")
      .then((list) => {
        const sessionsList = list || [];
        setSessions(sessionsList);
        const emptySession = sessionsList.find((s) => !s.messages || s.messages.length === 0);
        if (emptySession) {
          setSessionId(emptySession.id);
          setMessageHistory([]);
          window.history.replaceState({}, "", `/dashboard/chat?session=${emptySession.id}`);
        } else {
          postJson<Record<string, never>, { id: number }>("/chat/sessions", {})
            .then((res) => {
              setSessionId(res.id);
              setSessions((prev) => [{ id: res.id, user_id: 0, created_at: new Date().toISOString(), messages: [] }, ...prev]);
              window.history.replaceState({}, "", `/dashboard/chat?session=${res.id}`);
            })
            .catch((err: unknown) => {
              setError(err instanceof Error ? err.message : "Failed to create chat session");
            });
        }
      })
      .catch(() => {
        postJson<Record<string, never>, { id: number }>("/chat/sessions", {})
          .then((res) => {
            setSessionId(res.id);
            window.history.replaceState({}, "", `/dashboard/chat?session=${res.id}`);
          })
          .catch((err: unknown) => {
            setError(err instanceof Error ? err.message : "Failed to create chat session");
          });
      });
  }, []);

  useEffect(() => {
    if (sessionId != null) {
      getJson<SessionSummary[]>("/chat/sessions")
        .then((list) => setSessions(list || []))
        .catch(() => setSessions([]));
    }
  }, [sessionId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setError(null);
    setLoading(true);
    try {
      const res = await postJson<{ question: string; message_history?: {question:string,answer:string}[]}, { answer: string; sources: string[] }>(
        "/documents/query",
        { question: question.trim(), message_history: messageHistory },
      );
      setMessageHistory((prev) => [...prev, {
        question: question.trim(),
        answer: res.answer,
        sources: res.sources || [],
      }]);
      if (sessionId) {
        postJson(`/chat/sessions/${sessionId}/messages`, {question:question.trim(),answer:res.answer})
          .then(() => getJson<SessionSummary[]>("/chat/sessions").then((list) => setSessions(list || [])))
          .catch(() => {});
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
    setError(null);
    loadSessionMessages(id);
    window.history.replaceState({}, "", `/dashboard/chat?session=${id}`);
  }

  async function startNewChat() {
    try {
      const res = await postJson<Record<string, never>, { id: number }>("/chat/sessions", {});
      setSessionId(res.id);
      setMessageHistory([]);
      setError(null);
      setSessions((prev) => [{ id: res.id, user_id: 0, created_at: new Date().toISOString(), messages: [] }, ...prev]);
      window.history.replaceState({}, "", `/dashboard/chat?session=${res.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create chat");
    }
  }

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 border-r border-slate-800 bg-slate-900/30 flex flex-col">
        <a href="/dashboard" className="flex items-center gap-2 px-4 py-4 border-b border-slate-800">
          <img src="/OmniDocs.png" alt="OmniDocs" className="h-8 w-auto" />
          <span className="text-slate-400 hover:text-white text-sm">← Dashboard</span>
        </a>
        <button
          onClick={startNewChat}
          className="mx-3 mt-3 flex items-center gap-2 rounded-lg border border-slate-700 bg-transparent px-3 py-2.5 text-sm text-slate-300 hover:bg-slate-800 hover:text-white"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          New chat
        </button>
        <nav className="flex-1 overflow-y-auto px-3 py-3">
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => switchSession(s.id)}
              className={`mb-1 w-full rounded-lg px-3 py-2.5 text-left text-sm transition ${
                sessionId === s.id
                  ? "bg-slate-700 text-white"
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`}
              title={getSessionTitle(s, 80)}
            >
              {getSessionTitle(s)}
            </button>
          ))}
        </nav>
      </aside>

      {/* Main chat area */}
      <main className="flex-1 flex flex-col min-w-0">
        <div className="flex-1 overflow-y-auto px-6 py-8">
          <h1 className="text-xl font-semibold text-white mb-6">Ask about your documents</h1>
          {messageHistory.length > 0 && (
            <div className="mb-8 space-y-4">
            {messageHistory.map((item, index) => (
              <div key={index} className="rounded-lg border border-slate-700 bg-slate-900/50 p-4 space-y-2">
                <p className="text-sm font-medium text-slate-400">Q: {item.question}</p>
                <p className="text-slate-200 whitespace-pre-wrap">{item.answer}</p>
                {item.sources && item.sources.length > 0 && (
                  <p className="text-xs text-slate-500 mt-2">
                    <span className="font-medium text-slate-400">Sources: </span>
                    {item.sources.join(", ")}
                  </p>
                )}
              </div>
            ))}
          </div>
          )}

          {error && (
            <div className="rounded-md border border-red-800 bg-red-950/40 px-4 py-3 text-red-400 mb-6">
              {error}
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="shrink-0 border-t border-slate-800 px-6 py-4">
          <div className="relative flex items-center">
            <input
              type="text"
              placeholder="Ask about your documents..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={loading}
              className="w-full rounded-full border border-slate-700 bg-slate-900 pl-5 pr-14 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent disabled:opacity-60"
            />
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="absolute right-2 flex h-9 w-9 items-center justify-center rounded-full bg-emerald-500 text-slate-950 transition hover:bg-emerald-400 disabled:pointer-events-none disabled:opacity-40"
              title="Send"
            >
              {loading ? (
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-900/30 border-t-slate-900" />
              ) : (
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                </svg>
              )}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}