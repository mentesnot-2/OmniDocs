export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-950 px-6">
      <main className="flex flex-col items-center gap-8 text-center">
        <img
          src="/OmniDocs.png"
          alt="OmniDocs"
          className="h-32 w-auto"
        />
        <p className="max-w-lg text-slate-400">
          Universal RAG for multi-format documents. Upload PDFs, DOCX, and more — ask questions and get grounded answers.
        </p>
        <div className="flex gap-4">
          <a
            href="/login"
            className="rounded-md bg-emerald-500 px-6 py-2.5 font-medium text-slate-950 hover:bg-emerald-400"
          >
            Log in
          </a>
          <a
            href="/signup"
            className="rounded-md border border-slate-600 px-6 py-2.5 font-medium text-slate-200 hover:bg-slate-800"
          >
            Sign up
          </a>
        </div>
      </main>
    </div>
  );
}
