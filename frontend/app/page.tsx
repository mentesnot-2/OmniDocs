export default function Home() {
  return (
    <div className="min-h-screen bg-slate-950">
      {/* Hero */}
      <header className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 via-transparent to-cyan-500/5" />
        <div className="relative mx-auto max-w-6xl px-6 py-16 sm:py-24">
          <div className="flex flex-col items-center text-center">
            <img
              src="/OmniDocs.png"
              alt="OmniDocs"
              className="mb-8 h-28 w-auto sm:h-36"
            />
            <h1 className="mb-4 max-w-3xl text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl">
              Ask anything about{" "}
              <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                your documents
              </span>
            </h1>
            <p className="mb-10 max-w-2xl text-lg text-slate-400 sm:text-xl">
              Universal RAG for PDF, Word, Excel, and more. Upload, index, and get grounded answers with source citations — no more searching through files.
            </p>
            <div className="flex flex-col gap-4 sm:flex-row">
              <a
                href="/signup"
                className="rounded-lg bg-emerald-500 px-8 py-3.5 text-base font-semibold text-slate-950 shadow-lg shadow-emerald-500/25 transition hover:bg-emerald-400 hover:shadow-emerald-500/30"
              >
                Get started free
              </a>
              <a
                href="/login"
                className="rounded-lg border border-slate-600 bg-slate-800/50 px-8 py-3.5 text-base font-semibold text-white transition hover:border-slate-500 hover:bg-slate-800"
              >
                Log in
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Features */}
      <section className="border-t border-slate-800/50">
        <div className="mx-auto max-w-6xl px-6 py-16 sm:py-20">
          <h2 className="mb-12 text-center text-2xl font-semibold text-white sm:text-3xl">
            Built for teams who live in documents
          </h2>
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 transition hover:border-slate-700">
              <div className="mb-3 text-2xl">📄</div>
              <h3 className="mb-2 text-lg font-semibold text-white">Any format</h3>
              <p className="text-sm text-slate-400">
                PDF, DOCX, XLSX, CSV, HTML, Markdown — one place to search and ask.
              </p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 transition hover:border-slate-700">
              <div className="mb-3 text-2xl">🔍</div>
              <h3 className="mb-2 text-lg font-semibold text-white">Semantic search</h3>
              <p className="text-sm text-slate-400">
                Find answers by meaning, not keywords. Get relevant chunks and citations.
              </p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 transition hover:border-slate-700">
              <div className="mb-3 text-2xl">🔒</div>
              <h3 className="mb-2 text-lg font-semibold text-white">Your data only</h3>
              <p className="text-sm text-slate-400">
                Per-user isolation. Your documents stay yours — secure and private.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-slate-800/50">
        <div className="mx-auto max-w-4xl px-6 py-16 sm:py-20">
          <div className="rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 to-slate-900/50 p-8 text-center sm:p-12">
            <h2 className="mb-4 text-2xl font-semibold text-white sm:text-3xl">
              Ready to stop digging through files?
            </h2>
            <p className="mb-8 text-slate-400">
              Create an account and upload your first document in seconds.
            </p>
            <a
              href="/signup"
              className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-8 py-3.5 text-base font-semibold text-slate-950 shadow-lg shadow-emerald-500/25 transition hover:bg-emerald-400"
            >
              Sign up free
              <span className="text-lg">→</span>
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800/50 py-8">
        <div className="mx-auto max-w-6xl px-6 text-center text-sm text-slate-500">
          OmniDocs — Universal RAG for multi-format documents
        </div>
      </footer>
    </div>
  );
}
