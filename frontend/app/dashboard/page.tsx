"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { postFormData, postJson } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ id: number; email: string } | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  useEffect(() => {
    const raw = localStorage.getItem("omnidocs_user");
    if (raw) {
      try {
        setUser(JSON.parse(raw));
      } catch {
        router.push("/login");
      }
    } else {
      router.push("/login");
    }
  }, [router]);

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
        <h1 className="text-xl font-semibold text-white">OmniDocs</h1>
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