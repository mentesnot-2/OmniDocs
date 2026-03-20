"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { postFormData, getJson, postJson, deleteRequest } from "@/lib/api";

function formatDate(timestamp: number) {
  const d = new Date(timestamp * 1000);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  if (diff < 86400000) return "Today";
  if (diff < 172800000) return "Yesterday";
  return d.toLocaleDateString();
}

type UsageMetrics = {
  month: string;
  queries_this_month: number;
  uploads_this_month: number;
  storage: {
    used_bytes: number;
    limit_bytes: number;
    used_percent: number;
  };
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let value = bytes;
  let i = -1;
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024;
    i += 1;
  }
  return `${value.toFixed(value >= 100 ? 0 : 1)} ${units[i]}`;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ id: number; email: string; is_admin: boolean } | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [documents, setDocuments] = useState<{ filename: string; uploaded_at: number }[]>([]);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [usage, setUsage] = useState<UsageMetrics | null>(null);
  const [usageLoading, setUsageLoading] = useState(true);
  const [usageError, setUsageError] = useState<string | null>(null);

  async function loadUsage() {
    setUsageLoading(true);
    setUsageError(null);
    try {
      const usageRes = await getJson<UsageMetrics>("/usage/me");
      setUsage(usageRes);
    } catch (err: unknown) {
      setUsageError(err instanceof Error ? err.message : "Failed to load usage metrics.");
    } finally {
      setUsageLoading(false);
    }
  }

  async function loadDashboardData() {
    try {
      const me = await getJson<{ id: number; email: string; is_admin: boolean }>("/auth/me");
      setUser(me);
      const docsRes = await getJson<{ documents: { filename: string; uploaded_at: number }[] }>("/documents/");
      setDocuments(docsRes.documents || []);
      await loadUsage();
    } catch {
      setUser(null);
      router.push("/login");
    }
  }

  useEffect(() => {
    loadDashboardData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  async function handleDelete(filename: string) {
    if (!confirm(`Delete "${filename}"? This cannot be undone.`)) return;
    setDeleting(filename);
    try {
      await deleteRequest(`/documents/${encodeURIComponent(filename)}`);
      setDocuments((prev) => prev.filter((d) => d.filename !== filename));
      await loadUsage();
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Failed to delete document");
    } finally {
      setDeleting(null);
    }
  }

  async function handleLogout() {
    try {
      await postJson("/auth/logout", {});
    } catch {
      // ignore
    }
    router.push("/login");
  }

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      setUploadError("Please select a file");
      return;
    }
    setUploadError(null);
    setUploadSuccess(null);
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await postFormData("/documents/upload", formData);
      setUploadSuccess(`"${res.file_name}" indexed successfully.`);
      setFile(null);
      const docsRes = await getJson<{ documents: { filename: string; uploaded_at: number }[] }>("/documents/");
      setDocuments(docsRes.documents || []);
      await loadUsage();
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) setFile(f);
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0c0c0e]">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-emerald-500/30 border-t-emerald-400" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0c0c0e] text-slate-100">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-[#0c0c0e]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4">
          <a href="/dashboard" className="flex items-center gap-2">
            <img src="/OmniDocs.png" alt="OmniDocs" className="h-8 w-auto" />
          </a>
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-500">{user.email}</span>
            {user.is_admin && (
              <a
                href="/dashboard/admin"
                className="rounded-lg px-3 py-1.5 text-sm text-slate-400 transition hover:bg-white/5 hover:text-white"
              >
                Admin
              </a>
            )}
            <button
              onClick={handleLogout}
              className="rounded-lg px-3 py-1.5 text-sm text-slate-400 transition hover:bg-white/5 hover:text-white"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 pt-28 pb-20">
        {/* Welcome */}
        <div className="mb-12">
          <h1 className="text-2xl font-semibold tracking-tight text-white md:text-3xl">
            Your workspace
          </h1>
          <p className="mt-2 text-slate-500">
            Upload documents, then ask questions about them in natural language.
          </p>
        </div>

        {/* Usage metrics */}
        <section className="mb-10">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-medium uppercase tracking-wider text-slate-500">
              Usage
            </h2>
            <div className="flex items-center gap-3">
              {usage?.month && <span className="text-xs text-slate-600">{usage.month}</span>}
              <button
                type="button"
                onClick={loadUsage}
                className="rounded-md border border-white/10 px-2 py-1 text-xs text-slate-400 transition hover:bg-white/5 hover:text-white"
              >
                Refresh
              </button>
            </div>
          </div>

          {usageError && (
            <p className="mb-3 text-sm text-red-400">{usageError}</p>
          )}

          {usageLoading || !usage ? (
            <div className="grid gap-3 md:grid-cols-3">
              <div className="h-24 animate-pulse rounded-xl border border-white/5 bg-white/[0.03]" />
              <div className="h-24 animate-pulse rounded-xl border border-white/5 bg-white/[0.03]" />
              <div className="h-24 animate-pulse rounded-xl border border-white/5 bg-white/[0.03]" />
            </div>
          ) : (
            <div className="grid gap-3 md:grid-cols-3">
              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
                <p className="text-xs text-slate-500">Queries this month</p>
                <p className="mt-1 text-2xl font-semibold text-white">{usage.queries_this_month}</p>
              </div>

              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
                <p className="text-xs text-slate-500">Uploads this month</p>
                <p className="mt-1 text-2xl font-semibold text-white">{usage.uploads_this_month}</p>
              </div>

              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-slate-500">Storage</p>
                  {usage.storage.used_percent >= 80 && (
                    <span className="rounded bg-amber-500/20 px-2 py-0.5 text-[10px] uppercase tracking-wide text-amber-300">
                      Near limit
                    </span>
                  )}
                </div>
                <p className="mt-1 text-sm text-slate-300">
                  {formatBytes(usage.storage.used_bytes)} / {formatBytes(usage.storage.limit_bytes)}
                </p>
                <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-800">
                  <div
                    className={`h-full rounded-full ${
                      usage.storage.used_percent >= 90
                        ? "bg-red-400"
                        : usage.storage.used_percent >= 75
                          ? "bg-amber-400"
                          : "bg-emerald-400"
                    }`}
                    style={{ width: `${Math.min(100, usage.storage.used_percent)}%` }}
                  />
                </div>
                <p className="mt-2 text-xs text-slate-500">{usage.storage.used_percent.toFixed(1)}% used</p>
              </div>
            </div>
          )}
        </section>

        {/* Upload zone */}
        <section className="mb-16">
          <form
            onSubmit={handleUpload}
            onDrop={onDrop}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            className={`relative overflow-hidden rounded-2xl border-2 border-dashed transition-all duration-200 ${
              dragOver ? "border-emerald-500/50 bg-emerald-500/5" : "border-white/10 bg-white/[0.02] hover:border-white/20"
            }`}
          >
            <div className="flex flex-col items-center justify-center px-8 py-14">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-emerald-500/10">
                <svg className="h-7 w-7 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
              </div>
              <p className="text-center text-sm font-medium text-white">
                {file ? file.name : "Drop a file here, or click to browse"}
              </p>
              <p className="mt-1 text-center text-xs text-slate-500">
                PDF, DOCX, TXT, MD, CSV, XLSX, HTML, PPTX
              </p>
              <input
                type="file"
                accept=".pdf,.docx,.txt,.md,.csv,.xlsx,.html,.htm,.pptx"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="absolute left-0 right-0 top-0 h-24 cursor-pointer opacity-0"
              />
              <button
                type="submit"
                disabled={uploading || !file}
                className="mt-6 rounded-xl bg-emerald-500 px-6 py-2.5 text-sm font-medium text-slate-950 shadow-lg shadow-emerald-500/20 transition hover:bg-emerald-400 disabled:pointer-events-none disabled:opacity-40"
              >
                {uploading ? (
                  <span className="flex items-center gap-2">
                    <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-slate-900/30 border-t-slate-900" />
                    Indexing…
                  </span>
                ) : (
                  "Index document"
                )}
              </button>
            </div>
          </form>

          {uploadError && (
            <p className="mt-3 text-sm text-red-400">{uploadError}</p>
          )}
          {uploadSuccess && (
            <p className="mt-3 text-sm text-emerald-400">{uploadSuccess}</p>
          )}
        </section>

        {/* Documents */}
        <section>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-medium uppercase tracking-wider text-slate-500">
              Documents
            </h2>
            {documents.length > 0 && (
              <span className="text-xs text-slate-600">
                {documents.length} {documents.length === 1 ? "file" : "files"}
              </span>
            )}
          </div>

          {documents.length === 0 ? (
            <div className="rounded-2xl border border-white/5 bg-white/[0.02] px-8 py-16 text-center">
              <p className="text-slate-500">No documents yet.</p>
              <p className="mt-1 text-sm text-slate-600">
                Upload a file above to get started.
              </p>
            </div>
          ) : (
            <ul className="space-y-2">
              {documents.map((doc) => (
                <li
                  key={doc.filename}
                  className="group flex items-center gap-4 rounded-xl border border-white/5 bg-white/[0.02] px-4 py-3 transition hover:border-white/10 hover:bg-white/[0.04]"
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-800/50">
                    <svg className="h-5 w-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-white">{doc.filename}</p>
                    <p className="text-xs text-slate-500">{formatDate(doc.uploaded_at)}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDelete(doc.filename)}
                    disabled={deleting === doc.filename}
                    className="shrink-0 rounded-lg p-2 text-slate-400 opacity-0 transition hover:bg-red-500/10 hover:text-red-400 group-hover:opacity-100 disabled:opacity-50"
                    title="Delete"
                  >
                    {deleting === doc.filename ? (
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-red-500/30 border-t-red-400" />
                    ) : (
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                      </svg>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* Q&A CTA */}
        <section className="mt-16">
          <a
            href="/dashboard/chat"
            className="group flex items-center justify-between rounded-2xl border border-emerald-500/20 bg-emerald-500/5 px-6 py-5 transition hover:border-emerald-500/40 hover:bg-emerald-500/10"
          >
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/20">
                <svg className="h-6 w-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
                </svg>
              </div>
              <div>
                <p className="font-medium text-white">Ask questions</p>
                <p className="text-sm text-slate-500">
                  Query your documents with natural language
                </p>
              </div>
            </div>
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400 transition group-hover:bg-emerald-500/30 group-hover:text-emerald-300">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </span>
          </a>
        </section>
      </main>
    </div>
  );
}
