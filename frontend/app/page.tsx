const stats = [
  { value: "9+", label: "Document formats supported" },
  { value: "15 min", label: "Access token lifetime with silent refresh" },
  { value: "100%", label: "Grounded answers from retrieved context" },
];

const features = [
  {
    title: "Ask across every document",
    description: "Upload PDF, DOCX, PPTX, XLSX, CSV, Markdown, HTML, and TXT files into one searchable workspace.",
  },
  {
    title: "Grounded responses with sources",
    description: "OmniDocs answers from retrieved chunks so users can verify where each answer came from.",
  },
  {
    title: "Secure auth and session handling",
    description: "HttpOnly cookies, refresh tokens, route protection, email verification, and optional Google sign-in.",
  },
  {
    title: "Admin, support, and control",
    description: "Manage users, review support tickets, and control account access from admin-only endpoints.",
  },
  {
    title: "Usage analytics and plan controls",
    description: "Track monthly queries, uploads, storage usage, and enforce plan-based limits with upgrade paths.",
  },
  {
    title: "Production-friendly foundation",
    description: "Dockerized app, rate limiting, file-size checks, path traversal protection, and clean API boundaries.",
  },
];

const workflow = [
  {
    step: "01",
    title: "Upload and index",
    description: "Bring your docs in, chunk them, generate embeddings, and store them for fast semantic retrieval.",
  },
  {
    step: "02",
    title: "Ask naturally",
    description: "Use chat to ask product, technical, legal, or internal knowledge questions in plain language.",
  },
  {
    step: "03",
    title: "Act with confidence",
    description: "Review answers, see sources, monitor usage, and manage users or billing without leaving the app.",
  },
];

const plans = [
  {
    name: "Free",
    price: "$0",
    note: "For prototypes and personal workspaces",
    features: ["100 queries / month", "20 uploads / month", "100 MB storage", "Chat history and document search"],
    cta: "Start free",
  },
  {
    name: "Pro",
    price: "$29",
    note: "For teams that rely on document intelligence daily",
    features: ["5,000 queries / month", "1,000 uploads / month", "5 GB storage", "Billing portal and usage controls"],
    cta: "Upgrade to Pro",
    featured: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    note: "For scale, governance, and dedicated support",
    features: ["Custom limits", "Advanced support workflows", "Admin controls", "Deployment flexibility"],
    cta: "Talk to us",
  },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-[#060816] text-slate-100">
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(16,185,129,0.18),transparent_30%),radial-gradient(circle_at_80%_20%,rgba(59,130,246,0.18),transparent_28%),linear-gradient(to_bottom,#08101f,rgba(8,16,31,0.96))]" />
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-400/50 to-transparent" />

        <header className="relative z-10 mx-auto flex max-w-7xl items-center justify-between px-6 py-6">
          <a href="/" className="flex items-center gap-3">
            <img src="/OmniDocs.png" alt="OmniDocs" className="h-11 w-auto rounded-xl" />
            <div>
              <p className="text-sm font-semibold tracking-wide text-white">OmniDocs</p>
              <p className="text-xs text-slate-400">Document intelligence for modern teams</p>
            </div>
          </a>
          <nav className="hidden items-center gap-8 text-sm text-slate-300 md:flex">
            <a href="#features" className="transition hover:text-white">Features</a>
            <a href="#workflow" className="transition hover:text-white">Workflow</a>
            <a href="#pricing" className="transition hover:text-white">Pricing</a>
          </nav>
          <div className="flex items-center gap-3">
            <a
              href="/login"
              className="hidden rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200 transition hover:bg-white/10 sm:inline-flex"
            >
              Log in
            </a>
            <a
              href="/signup"
              className="inline-flex rounded-xl bg-emerald-400 px-4 py-2 text-sm font-medium text-slate-950 shadow-[0_0_40px_rgba(52,211,153,0.15)] transition hover:bg-emerald-300"
            >
              Start free
            </a>
          </div>
        </header>

        <section className="relative z-10 mx-auto grid max-w-7xl gap-14 px-6 pb-20 pt-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-center lg:pb-28 lg:pt-16">
          <div>
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-4 py-2 text-xs font-medium uppercase tracking-[0.22em] text-emerald-300">
              AI SaaS for knowledge-heavy teams
            </div>
            <h1 className="max-w-4xl text-5xl font-semibold tracking-tight text-white sm:text-6xl lg:text-7xl">
              Turn scattered documents into
              <span className="bg-gradient-to-r from-emerald-300 via-cyan-300 to-blue-300 bg-clip-text text-transparent"> instant answers</span>
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300 sm:text-xl">
              OmniDocs combines secure authentication, semantic retrieval, admin controls, and usage analytics in one elegant AI workspace.
            </p>
            <div className="mt-10 flex flex-col gap-4 sm:flex-row">
              <a
                href="/signup"
                className="inline-flex items-center justify-center rounded-2xl bg-emerald-400 px-6 py-3.5 text-base font-semibold text-slate-950 transition hover:bg-emerald-300"
              >
                Launch your workspace
              </a>
              <a
                href="/login"
                className="inline-flex items-center justify-center rounded-2xl border border-white/10 bg-white/5 px-6 py-3.5 text-base font-semibold text-white transition hover:bg-white/10"
              >
                Explore the app
              </a>
            </div>
            <div className="mt-10 grid gap-4 sm:grid-cols-3">
              {stats.map((stat) => (
                <div key={stat.label} className="rounded-2xl border border-white/8 bg-white/[0.03] p-4 backdrop-blur">
                  <p className="text-2xl font-semibold text-white">{stat.value}</p>
                  <p className="mt-1 text-sm text-slate-400">{stat.label}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="relative">
            <div className="absolute -inset-6 rounded-[2rem] bg-gradient-to-br from-emerald-400/20 via-cyan-400/10 to-blue-500/20 blur-3xl" />
            <div className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-slate-900/80 shadow-2xl shadow-black/30">
              <div className="border-b border-white/6 px-6 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-white">OmniDocs Workspace</p>
                    <p className="text-xs text-slate-400">Secure RAG, billing, admin, and analytics</p>
                  </div>
                  <span className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs text-emerald-300">
                    Live usage insights
                  </span>
                </div>
              </div>
              <div className="grid gap-6 p-6">
                <div className="grid gap-4 sm:grid-cols-[1.1fr_0.9fr]">
                  <div className="rounded-2xl border border-white/8 bg-[#0f1427] p-5">
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Question</p>
                    <p className="mt-3 text-sm leading-7 text-slate-200">
                      Summarize the key rollout risks from our architecture docs and list the files they came from.
                    </p>
                  </div>
                  <div className="rounded-2xl border border-white/8 bg-[#0c1820] p-5">
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Usage</p>
                    <div className="mt-4 space-y-3">
                      <div>
                        <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
                          <span>Queries this month</span>
                          <span>64 / 100</span>
                        </div>
                        <div className="h-2 rounded-full bg-white/8">
                          <div className="h-2 w-[64%] rounded-full bg-emerald-400" />
                        </div>
                      </div>
                      <div>
                        <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
                          <span>Storage usage</span>
                          <span>72 MB / 100 MB</span>
                        </div>
                        <div className="h-2 rounded-full bg-white/8">
                          <div className="h-2 w-[72%] rounded-full bg-cyan-400" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-5">
                  <div className="flex items-start gap-3">
                    <div className="mt-1 flex h-9 w-9 items-center justify-center rounded-full bg-emerald-400/15 text-emerald-300">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-4l-4 4v-4z" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white">Answer generated from retrieved chunks</p>
                      <p className="mt-2 text-sm leading-7 text-slate-300">
                        Main risks are token-type confusion, slash redirect auth leakage, and silent verification-email failures. Sources: `api/dependencies.py`, `api/routes/documents.py`, `api/utils/email.py`.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      <section id="features" className="border-t border-white/6 bg-[#070b18]">
        <div className="mx-auto max-w-7xl px-6 py-20">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-sm uppercase tracking-[0.26em] text-emerald-300">Product capabilities</p>
            <h2 className="mt-4 text-3xl font-semibold text-white sm:text-4xl">
              Built like a modern AI product, not a throwaway demo
            </h2>
            <p className="mt-4 text-slate-400">
              Every layer is designed to feel production-ready: secure auth, usage controls, admin tooling, and a polished end-user workflow.
            </p>
          </div>
          <div className="mt-14 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="rounded-3xl border border-white/8 bg-white/[0.03] p-6 transition duration-200 hover:-translate-y-0.5 hover:border-emerald-400/20 hover:bg-white/[0.045]"
              >
                <div className="mb-5 h-10 w-10 rounded-2xl bg-gradient-to-br from-emerald-400/20 to-cyan-400/20" />
                <h3 className="text-xl font-semibold text-white">{feature.title}</h3>
                <p className="mt-3 leading-7 text-slate-400">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="workflow" className="border-t border-white/6">
        <div className="mx-auto max-w-7xl px-6 py-20">
          <div className="grid gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
            <div>
              <p className="text-sm uppercase tracking-[0.26em] text-cyan-300">Workflow</p>
              <h2 className="mt-4 text-3xl font-semibold text-white sm:text-4xl">
                From raw documents to actionable answers in three steps
              </h2>
              <p className="mt-4 max-w-xl text-slate-400">
                The product flow stays simple for users, while the platform handles ingestion, retrieval, authentication, analytics, and plan limits behind the scenes.
              </p>
            </div>
            <div className="space-y-4">
              {workflow.map((item) => (
                <div key={item.step} className="rounded-3xl border border-white/8 bg-white/[0.03] p-6">
                  <div className="flex items-center gap-4">
                    <span className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-400/15 text-sm font-semibold text-emerald-300">
                      {item.step}
                    </span>
                    <div>
                      <h3 className="text-lg font-semibold text-white">{item.title}</h3>
                      <p className="mt-1 text-slate-400">{item.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section id="pricing" className="border-t border-white/6 bg-[#070b18]">
        <div className="mx-auto max-w-7xl px-6 py-20">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-sm uppercase tracking-[0.26em] text-emerald-300">Pricing-ready architecture</p>
            <h2 className="mt-4 text-3xl font-semibold text-white sm:text-4xl">
              Start free, scale with usage-aware plans
            </h2>
            <p className="mt-4 text-slate-400">
              OmniDocs already supports usage tracking, billing pages, plan limits, and upgrade-ready subscription workflows.
            </p>
          </div>
          <div className="mt-14 grid gap-6 lg:grid-cols-3">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`rounded-3xl border p-7 ${
                  plan.featured
                    ? "border-emerald-400/30 bg-gradient-to-b from-emerald-400/10 to-white/[0.03]"
                    : "border-white/8 bg-white/[0.03]"
                }`}
              >
                {plan.featured && (
                  <div className="mb-5 inline-flex rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-300">
                    Most popular
                  </div>
                )}
                <h3 className="text-2xl font-semibold text-white">{plan.name}</h3>
                <div className="mt-4 flex items-end gap-2">
                  <span className="text-4xl font-semibold text-white">{plan.price}</span>
                  {plan.price !== "Custom" && <span className="pb-1 text-sm text-slate-400">/ month</span>}
                </div>
                <p className="mt-3 min-h-12 text-sm leading-6 text-slate-400">{plan.note}</p>
                <ul className="mt-6 space-y-3 text-sm text-slate-300">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex gap-3">
                      <span className="mt-0.5 text-emerald-300">+</span>
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
                <a
                  href={plan.name === "Enterprise" ? "/login" : "/signup"}
                  className={`mt-8 inline-flex w-full items-center justify-center rounded-2xl px-4 py-3 text-sm font-medium transition ${
                    plan.featured
                      ? "bg-emerald-400 text-slate-950 hover:bg-emerald-300"
                      : "border border-white/10 bg-white/5 text-white hover:bg-white/10"
                  }`}
                >
                  {plan.cta}
                </a>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-white/6">
        <div className="mx-auto max-w-5xl px-6 py-20">
          <div className="overflow-hidden rounded-[2rem] border border-white/8 bg-[linear-gradient(135deg,rgba(16,185,129,0.14),rgba(10,15,29,0.9)_40%,rgba(59,130,246,0.16))] p-8 text-center sm:p-12">
            <p className="text-sm uppercase tracking-[0.26em] text-emerald-300">Ready to ship</p>
            <h2 className="mt-4 text-3xl font-semibold text-white sm:text-4xl">
              Replace document chaos with a clean AI workflow
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-slate-300">
              Launch a secure document assistant with authentication, billing hooks, analytics, admin workflows, and a polished user experience already in place.
            </p>
            <div className="mt-8 flex flex-col justify-center gap-4 sm:flex-row">
              <a
                href="/signup"
                className="inline-flex items-center justify-center rounded-2xl bg-emerald-400 px-6 py-3.5 text-base font-semibold text-slate-950 transition hover:bg-emerald-300"
              >
                Create your account
              </a>
              <a
                href="/login"
                className="inline-flex items-center justify-center rounded-2xl border border-white/10 bg-white/5 px-6 py-3.5 text-base font-semibold text-white transition hover:bg-white/10"
              >
                Go to dashboard
              </a>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-white/6 py-8">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-6 text-sm text-slate-500 sm:flex-row">
          <div className="flex items-center gap-3">
            <img src="/OmniDocs.png" alt="OmniDocs" className="h-8 w-auto rounded-lg" />
            <span>OmniDocs</span>
          </div>
          <div className="flex gap-6">
            <a href="#features" className="transition hover:text-slate-300">Features</a>
            <a href="#pricing" className="transition hover:text-slate-300">Pricing</a>
            <a href="/login" className="transition hover:text-slate-300">Login</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
