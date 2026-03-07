"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { postFormData, postJson, getJson, deleteRequest } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ id: number; email: string } | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [documents, setDocuments] = useState<{ filename: string; uploaded_at: number }[]>([]);
  const [deleting,setDeleting] = useState<string | null>(null);

  
  useEffect(() => {
    const raw = localStorage.getItem("omnidocs_user");
    if (raw) {
      try {
        setUser(JSON.parse(raw));
        getJson<{documents:{filename:string; uploaded_at:number}[]}>("/documents/").then((res) => setDocuments(res.documents || [])).catch(() => setDocuments([]))
      } catch {
        router.push("/login");
      }
    } else {
      router.push("/login");
    }
  }, [router]);

  async function handleDelete(filename:string) {
    if (!confirm(`Delete "${filename}"? This cannot be undone.`)) return;
    setDeleting(filename);
    try {
      await deleteRequest(`/documents/${encodeURIComponent(filename)}`);
      setDocuments((perv) => perv.filter((d) => d.filename !== filename));
    } catch (err: any) {
      setUploadError(err.message || "Failed to delete document");
    } finally {
      setDeleting(null);
    }
  }

  function handleLogout() {
    localStorage.removeItem("omnidocs_token");
    localStorage.removeItem("omnidocs_user");
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
      setUploadSuccess(`Uploaded "${res.file_name}" — ${res.chunk_indexed} chunks indexed.`);
      setFile(null);
      getJson<{documents:{filename:string, uploaded_at:number}[]}>("/documents/").then((res) => setDocuments(res.documents || []))
    } catch (err: any) {
      setUploadError(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <p className="text-slate-400">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 px-6 py-4 flex justify-between items-center">
        <a href="/dashboard" className="flex items-center gap-2">
          <img src="/OmniDocs.png" alt="OmniDocs" className="h-9 w-auto" />
        </a>
        <div className="flex items-center gap-4">
          <span className="text-slate-400 text-sm">{user.email}</span>
          <button
            onClick={handleLogout}
            className="text-sm text-slate-400 hover:text-white"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-8 space-y-8">
        <section>
          <h2 className="text-lg font-medium text-white mb-4">Upload document</h2>
          <form onSubmit={handleUpload} className="space-y-4">
            <input
              type="file"
              accept=".pdf,.docx,.txt,.md,.csv,.xlsx,.html,.htm"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-emerald-500/20 file:text-emerald-400 file:cursor-pointer"
            />
            {uploadError && (
              <p className="text-sm text-red-400">{uploadError}</p>
            )}
            {uploadSuccess && (
              <p className="text-sm text-emerald-400">{uploadSuccess}</p>
            )}
            <button
              type="submit"
              disabled={uploading || !file}
              className="rounded-md bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-medium px-4 py-2"
            >
              {uploading ? "Uploading..." : "Upload & index"}
            </button>
          </form>
        </section>
        <section>
          <h2 className="text-lg font-medium text-white mb-4">Your documents</h2>
          {documents.length === 0 ? (
            <p className="text-slate-400 text-sm">No documents uploaded yet.</p>
          ) : (
            <ul className="space-y-2">
            {documents.map((doc) => (
              <li key={doc.filename} className="flex items-center justify-between gap-2 rounded-lg border border-slate-800 bg-slate-900/30 px-3 py-2">
                <span className="text-slate-300 text-sm truncate">{doc.filename}</span>
                <button
                  type="button"
                  onClick={() => handleDelete(doc.filename)}
                  disabled={deleting === doc.filename}
                  className="shrink-0 text-xs text-red-400 hover:text-red-300 disabled:opacity-50"
                >
                  {deleting === doc.filename ? "Deleting..." : "Delete"}
                </button>
              </li>
            ))}
          </ul>
          )}
        </section>

        <section>
          <h2 className="text-lg font-medium text-white mb-4">Ask a question</h2>
          <p className="text-slate-400 text-sm">
            Upload documents above, then go to the Q&A page to ask questions.
          </p>
          <a
            href="/dashboard/chat"
            className="mt-2 inline-block text-emerald-400 hover:underline"
          >
            Go to Q&A →
          </a>
        </section>
      </main>
    </div>
  );
}