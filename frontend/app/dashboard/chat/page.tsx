"use client";

import { useState, useEffect, useRef } from "react";
import { getJson, postJson } from "@/lib/api";

type Msg = { role: string; content: string };
type SessionSummary = { id: number; user_id: number; created_at: string; messages: Msg[] };

function getSessionTitle(session: SessionSummary, maxLen = 32): string {
  const firstUser = session.messages?.find((m) => m.role === "user");
  const text = firstUser?.content?.trim();
  if (!text) return "New chat";
  return text.length <= maxLen ? text : text.slice(0, maxLen) + "…";
}

const SUGGESTIONS = [
  "What are the main features of my documents?",
  "Summarize the key points",
  "What documents do I have?",
];

export default function ChatPage() {
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messageHistory, setMessageHistory] = useState<{question: string; answer: string; sources?: string[]}[]>([]);
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  function loadSessionMessages(sid: number) {
    getJson<{ messages: Msg[] }>(`/chat/sessions/${sid}`)
      .then((res) => {
        const pairs: { question: string; answer: string; sources?: string[] }[] = [];
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
        setError(err instanceof Error ? err.message : "Failed to fetch chat");
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

    getJson<SessionSummary[]>("/chat/sessions")
      .then((list) => {
        const sessionsList = list || [];
        setSessions(sessionsList);
        const empty = sessionsList.find((s) => !s.messages || s.messages.length === 0);
        if (empty) {
          setSessionId(empty.id);
          setMessageHistory([]);
          window.history.replaceState({}, "", `/dashboard/chat?session=${empty.id}`);
        } else {
          postJson<Record<string, never>, { id: number }>("/chat/sessions", {})
            .then((res) => {
              setSessionId(res.id);
              setSessions((prev) => [{ id: res.id, user_id: 0, created_at: new Date().toISOString(), messages: [] }, ...prev]);
              window.history.replaceState({}, "", `/dashboard/chat?session=${res.id}`);
            })
            .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to create chat"));
        }
      })
      .catch(() => {
        postJson<Record<string, never>, { id: number }>("/chat/sessions", {})
          .then((res) => {
            setSessionId(res.id);
            window.history.replaceState({}, "", `/dashboard/chat?session=${res.id}`);
          })
          .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to create chat"));
      });
  }, []);

  useEffect(() => {
    if (sessionId != null) {
      getJson<SessionSummary[]>("/chat/sessions")
        .then((list) => setSessions(list || []))
        .catch(() => setSessions([]));
    }
  }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messageHistory, pendingQuestion, loading, error]);

  async function handleSubmit(e: React.FormEvent, suggestion?: string) {
    e.preventDefault();
    const q = suggestion || question.trim();
    if (!q) return;
    setError(null);
    setLoading(true);
    setQuestion("");
    setPendingQuestion(q);
    try {
      const res = await postJson<
        { question: string; message_history?: { question: string; answer: string }[] },
        { answer: string; sources: string[] }
      >("/documents/query", { question: q, message_history: messageHistory });
      setPendingQuestion(null);
      setMessageHistory((prev) => [...prev, { question: q, answer: res.answer, sources: res.sources || [] }]);
      if (sessionId) {
        postJson(`/chat/sessions/${sessionId}/messages`, { question: q, answer: res.answer })
          .then(() => getJson<SessionSummary[]>("/chat/sessions").then((list) => setSessions(list || [])))
          .catch(() => {});
      }
    } catch (err: unknown) {
      setPendingQuestion(null);
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
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
    <div className="flex h-screen bg-[#0f0f10] text-slate-100">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? "w-64" : "w-0"
        } shrink-0 overflow-hidden border-r border-white/5 bg-[#131314] transition-all duration-200 flex flex-col`}
      >
        <div className="flex items-center justify-between p-3 border-b border-white/5">
          <a href="/dashboard" className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-white/5 transition">
            <img src="/OmniDocs.png" alt="OmniDocs" className="h-7 w-auto" />
            <span className="text-xs text-slate-400">Dashboard</span>
          </a>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1.5 rounded-lg text-slate-400 hover:bg-white/5 hover:text-white transition"
            title={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        </div>
        <button
          onClick={startNewChat}
          className="m-3 flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-slate-200 hover:bg-white/10 hover:border-white/20 transition"
        >
          <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          New chat
        </button>
        <nav className="flex-1 overflow-y-auto px-2 pb-4">
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => switchSession(s.id)}
              className={`mb-1 w-full rounded-lg px-3 py-2.5 text-left text-sm transition ${
                sessionId === s.id ? "bg-white/10 text-white" : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
              }`}
              title={getSessionTitle(s, 60)}
            >
              {getSessionTitle(s)}
            </button>
          ))}
        </nav>
      </aside>

      {!sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(true)}
          className="fixed left-4 top-4 z-10 p-2 rounded-lg bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white transition"
          title="Show sidebar"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      )}

      {/* Main chat */}
      <main className="flex-1 flex flex-col min-w-0">
        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-3xl px-4 py-8">
            {messageHistory.length === 0 && !pendingQuestion && !loading ? (
              /* Empty state */
              <div className="flex flex-col items-center justify-center min-h-[50vh] text-center">
                <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10">
                  <svg className="h-7 w-7 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
                  </svg>
                </div>
                <h2 className="text-xl font-semibold text-white mb-2">How can I help you today?</h2>
                <p className="text-slate-500 text-sm mb-8 max-w-md">
                  Ask anything about your documents. I'll search through them and give you answers with sources.
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {SUGGESTIONS.map((s, i) => (
                    <button
                      key={i}
                      onClick={(e) => handleSubmit(e, s)}
                      className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-slate-300 hover:bg-white/10 hover:border-white/20 transition"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              /* Message list */
              <div className="space-y-6">
                {messageHistory.map((item, i) => (
                  <div key={i} className="space-y-4">
                    {/* User */}
                    <div className="flex gap-3 justify-end">
                      <div className="max-w-[85%] rounded-2xl rounded-br-md bg-emerald-500/20 px-4 py-3">
                        <p className="text-slate-100 whitespace-pre-wrap text-[15px] leading-relaxed">{item.question}</p>
                      </div>
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-500/30 text-emerald-400 text-sm font-medium">
                        U
                      </div>
                    </div>
                    {/* Assistant */}
                    <div className="flex gap-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-600/50 text-slate-300">
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
                        </svg>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="rounded-2xl rounded-bl-md bg-white/5 border border-white/5 px-4 py-3">
                          <p className="text-slate-200 whitespace-pre-wrap text-[15px] leading-relaxed">{item.answer}</p>
                          {item.sources && item.sources.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-white/5">
                              <p className="text-xs text-slate-500 mb-2">Sources</p>
                              <div className="flex flex-wrap gap-2">
                                {item.sources.map((source) => (
                                  <a
                                    key={source}
                                    href={`/dashboard?doc=${encodeURIComponent(source)}`}
                                    className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-xs text-emerald-300 hover:bg-emerald-500/20"
                                  >
                                    {source}
                                  </a>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {/* Pending user message (optimistic) */}
                {pendingQuestion && (
                  <div className="flex gap-3 justify-end">
                    <div className="max-w-[85%] rounded-2xl rounded-br-md bg-emerald-500/20 px-4 py-3">
                      <p className="text-slate-100 whitespace-pre-wrap text-[15px] leading-relaxed">{pendingQuestion}</p>
                    </div>
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-500/30 text-emerald-400 text-sm font-medium">
                      U
                    </div>
                  </div>
                )}

                {/* Loading indicator */}
                {loading && (
                  <div className="flex gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-600/50">
                      <svg className="h-4 w-4 animate-pulse text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5" />
                      </svg>
                    </div>
                    <div className="rounded-2xl rounded-bl-md bg-white/5 border border-white/5 px-4 py-3">
                      <div className="flex gap-1.5">
                        <span className="h-2 w-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: "0ms" }} />
                        <span className="h-2 w-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: "150ms" }} />
                        <span className="h-2 w-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: "300ms" }} />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {error && (
              <div className="mt-6 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
                {error}
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input area */}
        <div className="shrink-0 border-t border-white/5 bg-[#0f0f10] p-4">
          <div className="mx-auto max-w-3xl">
            <form onSubmit={handleSubmit} className="relative">
              <input
                type="text"
                placeholder="Message OmniDocs..."
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={loading}
                className="w-full rounded-2xl border border-white/10 bg-white/5 pl-5 pr-14 py-3.5 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/30 disabled:opacity-60 text-[15px]"
              />
              <button
                type="submit"
                disabled={loading || !question.trim()}
                className="absolute right-2 top-1/2 -translate-y-1/2 flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500 text-white transition hover:bg-emerald-400 disabled:opacity-40 disabled:pointer-events-none"
                title="Send"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                </svg>
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}
